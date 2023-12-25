import argparse
import boto3

from stack_deleter import StackDeleter


cloudformation_client = boto3.client('cloudformation')
cloudformation_client_local = boto3.session.Session().client(
    service_name='cloudformation',
    endpoint_url='http://localhost:4566'
)

def main():
    parser = argparse.ArgumentParser(
        prog='StackKiller',
        description='This program deletes an AWS stack along with all the resources that are related to it.')
    parser.add_argument('-s', '--stack', required=True, help='The name of the stack to delete.')
    parser.add_argument('-f', '--force', required=False, default=True,  action=argparse.BooleanOptionalAction,
                        help='Whether to force deletion of all resources or not, defaults to true.')
    parser.add_argument('-l', '--local', required=False, default=False, action=argparse.BooleanOptionalAction)
    args = parser.parse_args()
    stack_name = args.stack
    force_deletion = args.force
    local = args.local
    stack_deleter = StackDeleter(cloudformation_client)
    if local:
        stack_deleter = StackDeleter(cloudformation_client_local)
    stack_deleter.delete_stack(stack_name, force_deletion)


if __name__ == '__main__':
    main()
