# external imports
import threading
import consul
import requests
from nautilus.network import registry
from consul import Check
from flask import Flask
from flask_graphql import GraphQLView, GraphQL
from flask_login import LoginManager
# local imports
from nautilus.network.consumers import ActionConsumer

class Service:
    """
        This is the base class for all services that are part of a nautilus
        cloud. This class provides basic functionalities such as registration,
        responding to actions, and predictable api endpoints.

        Args:

            action_handler (optional, function): The callback function fired when
                an action is recieved. If None, the service does not connect to the
                action queue.

            auth (optional, bool, default = True): Whether or not the service should add
                authentication requirements.

            auto_register (optional, bool): Whether or not the service should
                register itself when ran

            configObject (optional, class): A python class to use for configuring the
                service.

            name (string): The name of the service. This will be used to
                register the service with the registry as act as the designator
                for a ServiceObjectType.

            schema (optional, graphql.core.type.GraphQLSchema): The GraphQL schema
                which acts as a basis for the external API. If None, no endpoints are
                added to the service.

        Example:

            .. code-block:: python

                from nautilus import Service
                from nautilus.api import create_model_schema
                from nautilus.network import CRUDHandler
                from nautilus.models import BaseModel


                class Model(BaseModel):
                    name = Column(Text)


                # you could also make your own
                api_schema = create_model_schema(Model)
                action_handler = CRUDHandler(Model)


                service = Service(
                    name = 'My Awesome Service',
                    schema = api_schema,
                    action_handler = action_handler
                )
    """

    def __init__(
            self,
            name,
            schema=None,
            action_handler=None,
            configObject=None,
            auto_register=True,
            auth=True,
    ):
        # base the service on a flask app
        self.app = Flask(__name__)

        self.name = name
        self.__name__ = name
        self.auto_register = auto_register
        self.auth = auth

        # apply any necessary flask app config
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

        # if there is a configObject
        if configObject:
            # apply the config object to the flask app
            self.app.config.from_object(configObject)

        # if there is an action consumer, create a wrapper for it
        self.action_consumer = ActionConsumer(action_handler=action_handler) \
                                                  if action_handler else None


        # setup various functionalities
        self.setup_db()
        self.setup_admin()
        self.setup_auth()
        self.setup_api(schema)


    def run(self,
            host='127.0.0.1',
            port=8000,
            debug=False,
            secret_key='supersecret',
            **kwargs
           ):

        # save command line arguments
        self.app.config['DEBUG'] = debug
        self.app.config['HOST'] = host
        self.app.config['PORT'] = port
        self.app.config['SECRET_KEY'] = secret_key

        # if the service needs to register itself
        if self.auto_register:
            # register with the service registry
            registry.keep_alive(self)

        # if we need to spin up an action consumer
        if self.action_consumer:
            # create a thread that will run the consumer
            action_thread = threading.Thread(target=self.action_consumer.run)
            # start the thread
            action_thread.start()

        # run the service at the designated port
        self.app.run(host=self.app.config['HOST'], port=self.app.config['PORT'])


    def stop(self):
        # if there is an action consumer
        if self.action_consumer:
            # stop the consumer
            self.action_consumer.stop()

        try:
            # if the service is responsible for registering itself
            if self.auto_register:
                # remove the service from the registry
                registry.deregister_service(self)
        except requests.exceptions.ConnectionError as error:
            pass

    def setup_db(self):
        # import the nautilus db configuration
        from nautilus.db import db
        # initialize the service app
        db.init_app(self.app)


    def use_blueprint(self, blueprint):
        """ Apply a flask blueprint to the internal application """
        self.app.register_blueprint(blueprint)


    def setup_auth(self):
        # if we are supposed to enable authentication for the service
        if self.auth:
            from nautilus.auth import init_service
            init_service(self)


    def setup_admin(self):
        from nautilus.admin import init_service
        init_service(self)


    def setup_api(self, schema=None):
        # if there is a schema for the service
        if schema:
            # configure the service api with the schema
            from nautilus.api import init_service
            init_service(self, schema=schema)


    def route(self, **options):
        """
            A wrapper over Flask's @app.route(**options).
        """

        return self.app.route(**options)

