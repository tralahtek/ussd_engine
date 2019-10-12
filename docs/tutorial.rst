=====================
Creating ussd screens
=====================

This document is a whirlwind tour of how to create ussd screens.

The strongest feature of ussd airflow is being able to create ussd screen via yaml files and not code.
This enables users with mininal coding knowledge to be able to design ussd screens.

In ussd airflow, customer journey are created via yaml files, with each section defining a USSD screen.
There are different types of screens, each type having its own rules on how to use it in a USSD application.

Common rules in creating any kind of screen

**Each screen has a field called "type"** apart from initial_screen

The following are types of screens and the rules related to them.

1. Initial Screen (type -> initial_screen)
------------------------------------------

.. automodule:: ussd.screens.initial_screen
    :members: InitialScreen

2. Input Screen (type -> input_screen)
--------------------------------------

.. automodule:: ussd.screens.input_screen
   :members: InputScreen

3. Menu Screen (type -> menu_screen)
------------------------------------

.. autoclass:: ussd.screens.menu_screen.MenuScreen


4. Quit Screen (type -> quit_screen)
------------------------------------

.. autoclass:: ussd.screens.quit_screen.QuitScreen


5. Http screen (type -> http_screen)
------------------------------------

.. autoclass:: ussd.screens.http_screen.HttpScreen

6. Router screen (type -> router_screen)
----------------------------------------

.. autoclass:: ussd.screens.router_screen.RouterScreen

7. Update session screen (type -> update_session_screen)
--------------------------------------------------------

.. autoclass:: ussd.screens.update_session_screen.UpdateSessionScreen

8. Custom screen (type -> custom_screen)
----------------------------------------

.. autoclass:: ussd.screens.custom_screen.CustomScreen

9. Function screen ( type -> function_screen )
----------------------------------------------

.. autoclass:: ussd.screens.function_screen.FunctionScreen


***Once you have created your USSD screens run the following code to validate the customer journey***

   .. code-block:: text

         python manage.py validate_ussd_journey /path/to/your/ussd/file.yaml

