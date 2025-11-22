"""
Jira context provider.
"""

import os
import json
import logging
from typing import List, Dict, Set, Tuple, Optional, Any
from pathlib import Path
from argparse import Namespace

from jira import JIRA

from .base import BaseContextProvider
from ..core.contexts.jira import JiraValidationContext
from ..core.models import FieldDefinition, ScreenType
from ..core.problem_types.base import ContextBuildFailure

logger = logging.getLogger(__name__)


class JiraContextProvider(BaseContextProvider[JiraValidationContext]):
    """
    Builds JiraValidationContext instances.

    Handles:
    - Loading config and credentials
    - Connecting to Jira (with caching)
    - Fetching all fields (cached)
    - Getting screen information (must handle pagination)
    - Expanding wildcards
    - Filtering by source/target projects
    """

    _jira_client: Optional[JIRA] = None
    _all_fields_cache: Optional[Dict[str, FieldDefinition]] = None
    
    # Fields that don't always show up in meta but are valid
    SPECIAL_SYSTEM_FIELDS = {'Comment', 'Attachment', 'Linked Issues', 'Components'}

    def __init__(self):
        super().__init__()

    def get_jira_client(self, args: Namespace) -> JIRA:
        """
        Returns a cached, authenticated Jira client instance.

        Connects only on the first call, using credentials from environment
        variables and configuration files.
        """
        if JiraContextProvider._jira_client:
            return JiraContextProvider._jira_client

        # Load .validate.yaml
        config_settings = {}
        validate_yaml_path = Path(".validate.yaml")
        if validate_yaml_path.exists():
            try:
                import yaml
                with open(validate_yaml_path, "r") as f:
                    yaml_data = yaml.safe_load(f)
                    config_settings = yaml_data.get("global", {})
            except Exception as e:
                logger.warning(f"Failed to load .validate.yaml: {e}")

        # Precedence: Env Var > .validate.yaml > Defaults
        jira_url = os.environ.get("JIRA_URL", config_settings.get("jira_url", "https://trinoorsupport.atlassian.net"))
        jira_email = os.environ.get("JIRA_EMAIL", "shaun.mitchell@trinoor.com")
        jira_token = os.environ.get("JIRA_TOKEN")

        if not jira_token:
            raise ValueError("JIRA_TOKEN environment variable is not set.")

        logger.info(f"Connecting to Jira at {jira_url}")
        client = JIRA(
            server=jira_url,
            basic_auth=(jira_email, jira_token)
        )
        JiraContextProvider._jira_client = client
        return client

    @classmethod
    def provides_context_type(cls) -> type[JiraValidationContext]:
        """Provides JiraValidationContext"""
        return JiraValidationContext

    @classmethod
    def register_args(cls, parser: Any) -> None:
        """Register Jira-specific arguments"""
        jira_group = parser.add_argument_group("Jira Context Options")
        jira_group.add_argument(
            "--jira-config",
            type=Path,
            help="Path to Jira mirroring config file"
        )
        jira_group.add_argument(
            "--source-project",
            action="append",
            help="Source project key (can be repeated, omit for all)"
        )
        jira_group.add_argument(
            "--target-project",
            action="append",
            help="Target project key (can be repeated, omit for all)"
        )
        jira_group.add_argument(
            "--source-issue-type",
            action="append",
            help="Source issue type name (can be repeated, omit for all)"
        )
        jira_group.add_argument(
            "--target-issue-type",
            action="append",
            help="Target issue type name (can be repeated, omit for all)"
        )

    @classmethod
    def get_required_args(cls) -> Set[str]:
        """
        jira_config is technically required, but can be inferred from 'target'.
        So we return empty set here and validate in build_contexts.
        """
        return set()

    def can_provide(self, args: Namespace) -> bool:
        """Can provide if --jira-config is set or target looks like Jira config"""
        if hasattr(args, "jira_config") and args.jira_config:
            return True

        if hasattr(args, "target") and args.target:
            target = Path(args.target)
            if target.suffix == ".json" and target.exists():
                try:
                    with open(target, 'r') as f:
                        data = json.load(f)
                    return self._looks_like_jira_config(data)
                except Exception:
                    pass

        return False

    def build_contexts(self, args: Namespace) -> List[JiraValidationContext]:
        """
        Build contexts for each source->target issue type pair.
        """
        config_path = args.jira_config or Path(args.target)
        if not config_path:
             raise ValueError("JiraContextProvider requires either --jira-config or a valid JSON target file.")
             
        logger.info(f"Loading config from {config_path}")
        with open(config_path, "r") as f:
            config_data = json.load(f)

        self.get_jira_client(args)

        if JiraContextProvider._all_fields_cache is None:
            logger.info("Fetching all field definitions from Jira")
            JiraContextProvider._all_fields_cache = self._get_all_field_definitions()
            logger.info(f"Cached {len(JiraContextProvider._all_fields_cache)} field definitions")

        pairs = self._expand_config_to_pairs(
            config_data,
            source_filters=args.source_project,
            target_filters=args.target_project,
            source_type_filters=args.source_issue_type,
            target_type_filters=args.target_issue_type
        )
        logger.info(f"Found {len(pairs)} source->target combinations to validate")

        contexts = []
        for source_proj, target_proj, source_type, target_type, mapping_config in pairs:
            logger.debug(
                f"Building context for {source_proj} {source_type} -> "
                f"{target_proj} {target_type}"
            )
            context = self._build_context_for_pair(
                config_path=config_path,
                config=config_data,
                source_project=source_proj,
                target_project=target_proj,
                source_issue_type=source_type,
                target_issue_type=target_type,
                mapping_config=mapping_config,
                args=args
            )
            if context:
                contexts.append(context)

        return contexts

    def _get_all_field_definitions(self) -> Dict[str, FieldDefinition]:
        # NOTE: The implementation of this method MUST handle API pagination.
        client = self.get_jira_client(Namespace())
        all_fields = client.fields()
        field_defs = {}
        for field in all_fields:
            field_def = FieldDefinition.from_jira_field(field)
            field_defs[field_def.id] = field_def
            field_defs[field_def.name] = field_def
        return field_defs

    def _expand_config_to_pairs(
        self,
        config: dict,
        source_filters: Optional[List[str]],
        target_filters: Optional[List[str]],
        source_type_filters: Optional[List[str]] = None,
        target_type_filters: Optional[List[str]] = None
    ) -> List[Tuple[str, str, str, str, dict]]:
        # Map (source, target, src_type, tgt_type) -> (priority, mapping_config)
        # Priority: 1 = specific, 0 = wildcard expansion
        pairs_map = {}
        
        logger.info(f"Filtering sources: {source_filters}")
        
        for source_proj, targets in config.items():
            if source_filters and source_proj not in source_filters:
                continue
            for target_proj, direction_config in targets.items():
                if target_filters and target_proj not in target_filters:
                    continue
                destination_type = direction_config.get("destination_type")
                for source_type, target_configs in direction_config.get("issue_types", {}).items():
                    # Expand source types
                    if source_type == "*":
                        try:
                            actual_source_types = self._get_all_issue_types(source_proj)
                        except Exception as e:
                            self.errors.append(ContextBuildFailure(
                                context_name=f"{source_proj} (wildcard expansion)",
                                exception=e
                            ))
                            logger.error(f"Failed to expand source type wildcard for {source_proj}: {e}")
                            continue
                    else:
                        actual_source_types = [source_type]
                    
                    for actual_source_type in actual_source_types:
                        if source_type_filters and actual_source_type not in source_type_filters:
                            continue
                            
                        for target_type, mapping_config in target_configs.items():
                            # Expand target types
                            actual_target_type = destination_type or target_type
                            if actual_target_type == "*": 
                                continue # Can't infer target type if both are wildcard and no destination_type
                            
                            if target_type_filters and actual_target_type not in target_type_filters:
                                continue
                            
                            key = (source_proj, target_proj, actual_source_type, actual_target_type)
                            priority = 1 if target_type != "*" else 0
                            
                            # If we haven't seen this pair, or if this is a specific config overwriting a wildcard
                            if key not in pairs_map or priority > pairs_map[key][0]:
                                pairs_map[key] = (priority, mapping_config)
                                
        # Convert map back to list of tuples
        return [(k[0], k[1], k[2], k[3], v[1]) for k, v in pairs_map.items()]

    def _build_context_for_pair(
        self, config_path: Path, config: dict, source_project: str, target_project: str,
        source_issue_type: str, target_issue_type: str, mapping_config: dict, args: Namespace
    ) -> Optional[JiraValidationContext]:
        try:
            client = self.get_jira_client(args)
            
            source_fields = self._get_project_fields(source_project, source_issue_type)
            target_fields = self._get_project_fields(target_project, target_issue_type)
            
            create_screen_fields, create_screen_id, create_screen_name = self._get_screen_fields(client, target_project, target_issue_type, ScreenType.CREATE)
            edit_screen_fields, edit_screen_id, edit_screen_name = self._get_screen_fields(client, target_project, target_issue_type, ScreenType.EDIT)
            view_screen_fields, _, _ = self._get_screen_fields(client, target_project, target_issue_type, ScreenType.VIEW)
            
            required_fields = self._get_required_fields(target_project, target_issue_type)
            
            source_issue_type_id = self._get_issue_type_id(client, source_project, source_issue_type)
            target_issue_type_id = self._get_issue_type_id(client, target_project, target_issue_type)

            return JiraValidationContext(
                target=str(config_path), args=args, config_path=config_path, config=config,
                source_project_key=source_project, target_project_key=target_project,
                source_issue_type=source_issue_type, target_issue_type=target_issue_type,
                all_fields=JiraContextProvider._all_fields_cache or {},
                source_available_fields=source_fields, target_available_fields=target_fields,
                target_required_fields=required_fields,
                target_create_screen_fields=create_screen_fields,
                target_edit_screen_fields=edit_screen_fields,
                target_view_screen_fields=view_screen_fields,
                target_create_screen_id=create_screen_id, target_create_screen_name=create_screen_name,
                target_edit_screen_id=edit_screen_id, target_edit_screen_name=edit_screen_name,
                source_issue_type_id=source_issue_type_id, target_issue_type_id=target_issue_type_id,
                mapping_config=mapping_config
            )
        except Exception as e:
            logger.error(f"Failed to build context for {source_project}->{target_project}: {e}")
            return None

    def _get_project_fields(self, project_key: str, issue_type_name: str) -> Dict[str, FieldDefinition]:
        client = self.get_jira_client(Namespace())
        fields = {}
        
        # 1. Get fields from Create Metadata
        try:
            meta = client.createmeta(projectKeys=project_key, issuetypeNames=issue_type_name, expand="projects.issuetypes.fields")
            if meta.get('projects'):
                project_meta = meta['projects'][0]
                if project_meta.get('issuetypes'):
                    issuetype_meta = project_meta['issuetypes'][0]
                    for field_id, field_info in issuetype_meta.get('fields', {}).items():
                        if field_id in (JiraContextProvider._all_fields_cache or {}):
                            fields[field_id] = (JiraContextProvider._all_fields_cache or {})[field_id]
        except Exception as e:
            logger.warning(f"Failed to fetch createmeta for {project_key}: {e}")

        # 2. Get fields from Edit Screen (often contains fields hidden from Create)
        try:
            edit_fields, _, _ = self._get_screen_fields(client, project_key, issue_type_name, ScreenType.EDIT)
            for field in edit_fields:
                fields[field.id] = field
        except Exception as e:
            logger.warning(f"Failed to fetch edit screen fields for {project_key}: {e}")

        # 3. Add Special System Fields if they exist in the global cache
        for special_name in self.SPECIAL_SYSTEM_FIELDS:
            # Find ID for name
            # This is inefficient but safe. We iterate the cache.
            if JiraContextProvider._all_fields_cache:
                for f in JiraContextProvider._all_fields_cache.values():
                    if f.name == special_name:
                        fields[f.id] = f
                        break
        
        return fields

    def _get_screen_fields(self, client: JIRA, project_key: str, issue_type_name: str, screen_type: str) -> Tuple[Set[FieldDefinition], str, str]:
        """
        Get fields on a specific screen (create/edit/view).
        """
        try:
            project_id = self._get_project_id(client, project_key)
            issue_type_id = self._get_issue_type_id(client, project_key, issue_type_name)
            
            it_screen_scheme_id = self._get_issue_type_screen_scheme_id(client, project_id)
            screen_scheme_id = self._get_screen_scheme_id_for_issue_type(client, it_screen_scheme_id, issue_type_id)
            
            # Map ScreenType to Jira operation names
            operation_map = {
                ScreenType.CREATE: "create",
                ScreenType.EDIT: "edit",
                ScreenType.VIEW: "view"
            }
            operation = operation_map.get(screen_type, "default")
            
            screen_id, screen_name = self._get_screen_id_for_operation(client, screen_scheme_id, operation)
            
            if not screen_id:
                return set(), "unknown", "unknown"
                
            fields = self._get_fields_for_screen(client, screen_id)
            return fields, str(screen_id), screen_name
            
        except Exception as e:
            logger.warning(f"Failed to get screen fields for {project_key} {issue_type_name} {screen_type}: {e}")
            return set(), "unknown", "unknown"

    def _get_required_fields(self, project_key: str, issue_type_name: str) -> Set[FieldDefinition]:
        client = self.get_jira_client(Namespace())
        meta = client.createmeta(projectKeys=project_key, issuetypeNames=issue_type_name, expand="projects.issuetypes.fields")
        required_fields = set()
        if not meta.get('projects'): return required_fields
        
        project_meta = meta['projects'][0]
        issuetype_meta = project_meta['issuetypes'][0]

        for field_id, field_info in issuetype_meta['fields'].items():
            if field_info.get('required', False):
                if field_id in (JiraContextProvider._all_fields_cache or {}):
                    required_fields.add((JiraContextProvider._all_fields_cache or {})[field_id])
        return required_fields

    def _get_all_issue_types(self, project_key: str) -> List[str]:
        client = self.get_jira_client(Namespace())
        project = client.project(project_key)
        return [it.name for it in project.issueTypes if not it.subtask]

    def _get_issue_type_id(self, client: JIRA, project_key: str, issue_type_name: str) -> str:
        project = client.project(project_key)
        for it in project.issueTypes:
            if it.name == issue_type_name:
                return it.id
        raise ValueError(f"Issue type {issue_type_name} not found in {project_key}")

    def _get_issue_type_screen_scheme_id(self, client: JIRA, project_id: str) -> str:
        # Use raw API because jira-python might not have this specific helper
        url = f"{client._options['server']}/rest/api/2/issuetypescreenscheme/project?projectId={project_id}"
        resp = client._session.get(url)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("values"):
            raise ValueError(f"No issue type screen scheme found for project {project_id}")
        return data["values"][0]["issueTypeScreenScheme"]["id"]

    def _get_screen_scheme_id_for_issue_type(self, client: JIRA, it_screen_scheme_id: str, issue_type_id: str) -> str:
        url = f"{client._options['server']}/rest/api/2/issuetypescreenscheme/mapping?issueTypeScreenSchemeId={it_screen_scheme_id}"
        # Handle pagination if needed, but mappings are usually few
        resp = client._session.get(url)
        resp.raise_for_status()
        data = resp.json()
        
        default_scheme = None
        for mapping in data.get("values", []):
            if mapping["issueTypeId"] == issue_type_id:
                return mapping["screenSchemeId"]
            if mapping["issueTypeId"] == "default":
                default_scheme = mapping["screenSchemeId"]
        
        if default_scheme:
            return default_scheme
        raise ValueError(f"No screen scheme mapping found for issue type {issue_type_id}")

    def _get_screen_id_for_operation(self, client: JIRA, screen_scheme_id: str, operation: str) -> Tuple[Optional[str], str]:
        # Iterate pages to find screen scheme
        start_at = 0
        max_results = 50
        while True:
            url = f"{client._options['server']}/rest/api/2/screenscheme?startAt={start_at}&maxResults={max_results}"
            resp = client._session.get(url)
            resp.raise_for_status()
            data = resp.json()
            
            for scheme in data.get("values", []):
                if str(scheme["id"]) == str(screen_scheme_id):
                    screens = scheme.get("screens", {})
                    screen_id = screens.get(operation, screens.get("default"))
                    return screen_id, scheme.get("name", "unknown")
            
            if data.get("isLast", True):
                break
            start_at += max_results
            
        # Try direct access if not found in list (sometimes works for hidden schemes)
        try:
            url = f"{client._options['server']}/rest/api/2/screenscheme/{screen_scheme_id}"
            resp = client._session.get(url)
            if resp.ok:
                scheme = resp.json()
                screens = scheme.get("screens", {})
                screen_id = screens.get(operation, screens.get("default"))
                return screen_id, scheme.get("name", "unknown")
        except Exception:
            pass
            
        return None, "unknown"

    def _get_fields_for_screen(self, client: JIRA, screen_id: str) -> Set[FieldDefinition]:
        fields_found = set()
        url = f"{client._options['server']}/rest/api/2/screens/{screen_id}/tabs"
        resp = client._session.get(url)
        resp.raise_for_status()
        tabs = resp.json()
        
        for tab in tabs:
            tab_id = tab["id"]
            tab_url = f"{client._options['server']}/rest/api/2/screens/{screen_id}/tabs/{tab_id}/fields"
            tab_resp = client._session.get(tab_url)
            tab_resp.raise_for_status()
            tab_fields = tab_resp.json()
            
            for field in tab_fields:
                # Map back to our FieldDefinition
                # tab_fields returns basic info: {id: '...', name: '...'}
                # We should look up the full definition from our cache
                field_id = field["id"]
                if JiraContextProvider._all_fields_cache and field_id in JiraContextProvider._all_fields_cache:
                    fields_found.add(JiraContextProvider._all_fields_cache[field_id])
                else:
                    # Fallback if not in cache (shouldn't happen often)
                    fields_found.add(FieldDefinition(
                        id=field_id,
                        name=field["name"],
                        schema={},
                        custom=field_id.startswith("customfield")
                    ))
        return fields_found

    @staticmethod
    def _looks_like_jira_config(data: dict) -> bool:
        """Heuristic: does this look like a Jira mirroring config?"""
        for key, value in data.items():
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    if isinstance(subvalue, dict):
                        if "issue_types" in subvalue or "mirrored_fields" in subvalue:
                            return True
        return False
