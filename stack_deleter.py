from botocore.exceptions import ClientError
from enum import Enum


class StackStatus(Enum):
    DELETE_IN_PROGRESS = 1,
    DELETE_COMPLETE = 2,
    DELETE_FAILED = 3,
    NONEXISTENT = 4,
    DIFFERENT_STATE = 5,


class StackDeleter:
    def __init__(self, cloudformation_client):
        self.cloudformation_client = cloudformation_client

    def delete_stack(self, stack_name: str, force_deletion: bool, max_wait_time: int):
        if not force_deletion:
            print(f'Deleting stack {stack_name}.')
            stack_status = self._delete_stack(stack_name, max_wait_time)
            match stack_status:
                case StackStatus.DELETE_COMPLETE:
                    print(f'Stack {stack_name} deleted successfully.')
                case StackStatus.DELETE_FAILED:
                    delete_failed_resources = map(
                        lambda resource: resource['PhysicalResourceId'],
                        list(filter(
                            lambda resource: resource['ResourceStatus'] == 'DELETE_FAILED',
                            self._list_stack_resources(stack_name))))
                    if delete_failed_resources:
                        self.cloudformation_client.delete_stack(StackName=stack_name,
                                                                RetainResources=delete_failed_resources)

    def _delete_stack(self, stack_name: str, max_wait_time: int) -> StackStatus:
        self.cloudformation_client.delete_stack(StackName=stack_name)
        try:
            self.cloudformation_client.get_waiter(StackName='stack_delete_complete',
                                                  WaiterConfig={
                                                      'MaxAttempts': max_wait_time / 30
                                                  }).wait(StackName=stack_name)
        except ClientError:
            stack_status = self._get_stack_status(stack_name)
            if stack_status == StackStatus.DELETE_IN_PROGRESS:
                return StackStatus.DELETE_IN_PROGRESS
            raise
        stack_status = self._get_stack_status(stack_name)
        return stack_status

    def _list_stack_resources(self, stack_name: str) -> list:
        resources = []
        next_token = None
        while True:
            list_response = self.cloudformation_client.list_stack_resources(StackName=stack_name, NextToken=next_token)
            resources.extend(list_response['StackResourceSummaries'])
            if 'NextToken' not in list_response:
                break
            next_token = list_response['NextToken']
        return resources

    def _get_stack_status(self, stack_name: str) -> StackStatus:
        try:
            status = self.cloudformation_client.describe_stacks(StackName=stack_name)['Stacks'][0]['StackStatus']
            match status:
                case 'DELETE_IN_PROGRESS':
                    return StackStatus.DELETE_IN_PROGRESS
                case 'DELETE_COMPLETE':
                    return StackStatus.DELETE_COMPLETE
                case 'DELETE_FAILED':
                    return StackStatus.DELETE_FAILED
            return StackStatus.DIFFERENT_STATE
        except ClientError as error:
            error_message = error.response['Error']['Message']
            if error_message.endswith('does not exist'):
                return StackStatus.NONEXISTENT
            raise
