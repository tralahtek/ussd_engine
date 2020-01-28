from ..journey_store import JourneyStore
import boto3
from structlog import get_logger
from botocore.config import Config
from copy import deepcopy
from boto3.dynamodb.conditions import Key
import os

BOTO_CORE_CONFIG = os.environ.get('BOTO_CORE_CONFIG', None)
USE_LOCAL_DYNAMODB_SERVER = os.environ.get('USE_LOCAL_DYNAMODB_SERVER', False)

logger = get_logger(__name__)

# We'll find some better way to do this.
_DYNAMODB_CONN = None
_DYNAMODB_TABLE = {}

# defensive programming if config has been defined
# make sure it's the correct format.
if BOTO_CORE_CONFIG:
    assert isinstance(BOTO_CORE_CONFIG, Config)

dynamo_kwargs = dict(
    service_name='dynamodb',
    config=BOTO_CORE_CONFIG
)


def dynamodb_connection_factory(low_level=False, endpoint=None):
    """
    Since SessionStore is called for every single page view, we'd be
    establishing new connections so frequently that performance would be
    hugely impacted. We'll lazy-load this here on a per-worker basis. Since
    boto3.resource.('dynamodb')objects are state-less (aside from security
    tokens), we're not too concerned about thread safety issues.
    """
    boto_config = deepcopy(dynamo_kwargs)
    if endpoint is not None:
        boto_config["endpoint_url"] = endpoint

    if low_level:
        return boto3.client(**boto_config)

    global _DYNAMODB_CONN

    if not _DYNAMODB_CONN:
        logger.debug("Creating a DynamoDB connection.")
        _DYNAMODB_CONN = boto3.resource(**boto_config)
    return _DYNAMODB_CONN


def dynamodb_table(table: str, endpoint=None):
    global _DYNAMODB_TABLE

    if not _DYNAMODB_TABLE.get(table):
        _DYNAMODB_TABLE[table] = dynamodb_connection_factory(endpoint=endpoint).Table(table)
    return _DYNAMODB_TABLE[table]


def create_table(table_name: str):
    params = {
        'TableName': table_name,
        'KeySchema': [
            {'AttributeName': "username", 'KeyType': "HASH"},  # Partition key
            {'AttributeName': "journeyAndVersion", 'KeyType': "RANGE"}  # Sort key
        ],
        'AttributeDefinitions': [
            {'AttributeName': "username", 'AttributeType': "S"},
            {'AttributeName': "journeyAndVersion", 'AttributeType': "S"}
        ],
        'ProvisionedThroughput': {
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    }

    dynamodb = dynamodb_connection_factory(low_level=True, endpoint="http://dynamodb:8000")
    # Create the table
    dynamodb.create_table(**params)

    # Wait for the table to exist before exiting
    print('Waiting for', table_name, '...')
    waiter = dynamodb.get_waiter('table_exists')
    waiter.wait(TableName=table_name)


def delete_table(table_name: str):
    connection = dynamodb_connection_factory(low_level=True, endpoint="http://dynamodb:8000")
    connection.delete_table(
        TableName=table_name
    )


def append_dynamo_key_with_user(func):
    def wrapper(*args, **kwargs):
        # we need to append the parameter name with user
        # first parameter is instance i.e self
        # second parameter is name
        if not args[1].startswith("{}#".format(args[0].user)):
            args = list(args)
            args[1] = "{0}#{1}".format(args[0].user, args[1])
            args = tuple(args)
        return func(*args, **kwargs)

    return wrapper


class DynamoDb(JourneyStore):
    edit_mode_version = "-1"
    hash_key = "username"
    sort_key = "journeyAndVersion"

    def __init__(self, table_name, endpoint=None, user="default"):
        self.table_name = table_name
        self.table = dynamodb_table(table_name, endpoint=endpoint)
        self.user = user

    @staticmethod
    def _sort_key_journey(name):
        return "{0}#".format(name)

    @staticmethod
    def _sort_key_version(version):
        return "{0}#".format(version)

    def _generate_sort_key(self, name, version):
        return "{0}{1}".format(self._sort_key_journey(name), self._sort_key_version(version))

    def _get(self, name, version, screen_name, **kwargs):
        screen_kwarg = {}
        if screen_name is not None:
            screen_kwarg["ProjectionExpression"] = screen_name

        if version is None:
            response = self.table.query(
                KeyConditionExpression=Key(self.hash_key).eq(self.user) &
                                       Key(self.sort_key).begins_with(self._sort_key_journey(name)),
                **kwargs
            )
            item = response.get("Items")[-1]
        else:
            key = {
                self.hash_key: self.user,
                self.sort_key: self._generate_sort_key(name, version)
            }

            response = self.table.get_item(Key=key, **screen_kwarg)
            item = response.get('Item')

        if item:
            if item.get(self.hash_key):
                del item[self.hash_key]
            if item.get(self.sort_key):
                del item[self.sort_key]

            if screen_name:
                item = item.get(screen_name)
        return item or None

    def _get_all_journey_version(self, name):
        results = {}
        for i in self._query(name):
            version = i[self.sort_key].split("#")[1]
            del i[self.hash_key]
            del i[self.sort_key]
            results[version] = i
        return results

    def _query(self, name, **kwargs):
        response = self.table.query(
            KeyConditionExpression=Key(self.hash_key).eq(self.user) &
                                   Key(self.sort_key).begins_with(self._sort_key_journey(name)),
            **kwargs
        )
        return response.get('Items')

    def _save(self, name, journey, version):
        item = {
            self.hash_key: self.user,
            self.sort_key: self._generate_sort_key(name, version)
        }
        item.update(journey)

        response = self.table.put_item(
            Item=item
        )

    def _delete(self, name, version=None):
        items = [
            {
                self.hash_key: self.user,
                self.sort_key: self._generate_sort_key(name, version)
            }
        ]
        if version is None:
            items = self._query(name,
                                **{"ProjectionExpression": "{0}, {1}".format(self.hash_key, self.sort_key)})

        with self.table.batch_writer() as batch:
            for i in items:
                batch.delete_item(
                    Key={
                        self.hash_key: i[self.hash_key],
                        self.sort_key: i[self.sort_key]
                    }
                )

    def _all(self):
        response = self.table.query(
            KeyConditionExpression=Key(self.hash_key).eq(self.user)
        )

        results = dict()
        for i in response.get('Items'):
            name, version, others = i[self.sort_key].split("#")

            if not results.get(name):
                results[name] = {}

            del i[self.hash_key]
            del i[self.sort_key]
            results[name][version] = i

        return results

    def flush(self):
        all_records = self.table.scan()
        for i in all_records['Items']:
            self._delete(i[self.hash_key], i[self.sort_key])
