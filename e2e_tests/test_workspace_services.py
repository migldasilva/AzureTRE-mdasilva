import pytest

import config
from helpers import check_aad_auth_redirect
from resources.resource import disable_and_delete_resource, post_resource
from resources import strings

pytestmark = pytest.mark.asyncio

workspace_services = [
    strings.AZUREML_SERVICE,
    # strings.INNEREYE_SERVICE,
    strings.GITEA_SERVICE,
    strings.MLFLOW_SERVICE,
    strings.MYSQL_SERVICE,
    strings.HEALTH_SERVICE,
]


@pytest.mark.extended
@pytest.mark.timeout(75 * 60)
async def test_create_guacamole_service_into_base_workspace(verify, setup_test_workspace) -> None:
    workspace_path, workspace_id, workspace_owner_token = setup_test_workspace

    service_payload = {
        "templateName": strings.GUACAMOLE_SERVICE,
        "properties": {
            "display_name": "Workspace service test",
            "description": "Workspace service for E2E test"
        }
    }

    workspace_service_path, workspace_service_id = await post_resource(service_payload, f'/api{workspace_path}/{strings.API_WORKSPACE_SERVICES}', workspace_owner_token, verify)

    await ping_guacamole_workspace_service(workspace_id, workspace_service_id, verify)

    # patch the guac service. we'll just update the display_name but this will still force a full deployment run
    # and essentially terraform no-op
    patch_payload = {
        "properties": {
            "display_name": "Updated Guac Name",
        }
    }

    await post_resource(patch_payload, f'/api{workspace_service_path}', workspace_owner_token, verify, method="PATCH")

    user_resource_payload = {
        "templateName": strings.GUACAMOLE_WINDOWS_USER_RESOURCE,
        "properties": {
            "display_name": "My VM",
            "description": "Will be using this VM for my research",
            "os_image": "Windows 10"
        }
    }

    user_resource_path, _ = await post_resource(user_resource_payload, f'/api{workspace_service_path}/{strings.API_USER_RESOURCES}', workspace_owner_token, verify, method="POST")

    await disable_and_delete_resource(f'/api{user_resource_path}', workspace_owner_token, verify)

    await disable_and_delete_resource(f'/api{workspace_service_path}', workspace_owner_token, verify)


@pytest.mark.extended_aad
@pytest.mark.timeout(75 * 60)
async def test_create_guacamole_service_into_aad_workspace(verify, setup_test_aad_workspace) -> None:
    """This test will create a Guacamole service but will create a workspace and automatically register the AAD Application"""
    workspace_path, workspace_id, workspace_owner_token = setup_test_aad_workspace

    workspace_service_payload = {
        "templateName": strings.GUACAMOLE_SERVICE,
        "properties": {
            "display_name": "Workspace service test",
            "description": "Workspace service for E2E test"
        }
    }

    workspace_service_path, workspace_service_id = await post_resource(workspace_service_payload, f'/api{workspace_path}/{strings.API_WORKSPACE_SERVICES}', workspace_owner_token, verify)

    await ping_guacamole_workspace_service(workspace_id, workspace_service_id, verify)

    await disable_and_delete_resource(f'/api{workspace_service_path}', workspace_owner_token, verify)


async def ping_guacamole_workspace_service(workspace_id, workspace_service_id, verify) -> None:
    short_workspace_id = workspace_id[-4:]
    short_workspace_service_id = workspace_service_id[-4:]
    endpoint = f"https://guacamole-{config.TRE_ID}-ws-{short_workspace_id}-svc-{short_workspace_service_id}.azurewebsites.net/guacamole"

    await check_aad_auth_redirect(endpoint, verify)


@pytest.mark.workspace_services
@pytest.mark.timeout(45 * 60)
@pytest.mark.parametrize("template_name", workspace_services)
async def test_install_workspace_service(template_name, verify, setup_test_workspace) -> None:
    workspace_path, workspace_id, workspace_owner_token = setup_test_workspace

    service_payload = {
        "templateName": template_name,
        "properties": {
            "display_name": f"{template_name} test",
            "description": "Workspace service for E2E test"
        }
    }

    workspace_service_path, workspace_service_id = await post_resource(service_payload, f'/api{workspace_path}/{strings.API_WORKSPACE_SERVICES}', workspace_owner_token, verify)

    await disable_and_delete_resource(f'/api{workspace_service_path}', workspace_owner_token, verify)
