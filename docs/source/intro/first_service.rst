Your First Service
===================

Services are the fundamental building blocks for cloud applications powered by
nautilus. Let's begin by creating a directory with an empty file somewhere on
your computer for us to use as a playground.

.. code-block:: bash

    $ mkdir nautilus_playground && \
            cd nautilus_playground && \
            touch server.py

Now that we have a file, let's make our first service. Keep in mind, that
this section is meant to illustrate the various parts of a service, as you
will see in the next section, the service we are about to construct can be
much more succintly created using one of nautilus's pre-packaged services.
Open server.py in your favorite text editor and copy and paste the following:

.. code-block:: python

    from nautilus import Service

    class RecipeService(Service): pass

    if __name__ == '__main__':
        # create an instance of the service
        service = RecipeService()

        # create a manager for the service
        manager = ServiceManager(RecipeService)

        if __name__ == '__main__':
            manager.run()


Test that this works by executing this script in your console:

.. code-block:: bash

    $ python3 ./server.py runserver


If it complains about permissions, try running ``sudo chmod u+x ./server.py``.


Right now, our service is nothing more than a python process. It doesn't react
to the outside world, it doesn't store any data, nor does it provide
anything for another service to use - let's change that.

Responding to Actions
-----------------------

Now that we have a service, we can start adding some functionality to it. In the
nautilus architecture, services are triggered to perform certain actions by
events. We describe how the service responds to those events through
the ``Action Handler``, a class record that holds the event configuration
as well as its behavior:


.. code-block:: python

    from nautilus.network import ActionHandler

    class PrintHandler(ActionHandler):

        async def handle_action(self, action_type, payload, props):
            print('hello world!')

The primary method of an ActionHandler takes three arguments: ``action_type``,
``payload``, and ``props``. ``Action_type`` identifies the event and
``payload`` provides the associated data. Ignore ``props`` for now.

Passing the Action handler to the service takes a single line:

.. code-block:: python

    from nautilus import Service, ServiceManager
    from nautilus.network import ActionHandler


    class PrintHandler(ActionHandler):

        async def handle_action(self, action_type, payload, props):
            print(action_type, payload)


    class MyService(Service):
        action_handler = PrintHandler


    manager = ServiceManager(RecipeService)

    if __name__ == '__main__':
        manager.run()


Let's test your service using the command line interface provided by nautilus.
Open up a new terminal and execute:

.. code-block:: bash

    $ naut publish -p "hello world"

You should see the message in your running service's console. This pattern
can be made to acommodate most situations. For example, if you had
some special behavior that you wanted your service to do (like send an email),
you would triger that behavior by firing a "send_email" action type and
responding appropriately:

.. code-block:: python

    from nautilus.network import ActionHandler

    class EmailActionHandler(ActionHandler):

        async def handle_action(self, action_type, payload, props):

            if action_type == 'send_email':
                # send the body of the action as the email
                send_email(payload)



Congratulations! You have finally pieced together a complete nautilus service.
In the next section you will learn how to create services that
manage and persist database entries for your application.