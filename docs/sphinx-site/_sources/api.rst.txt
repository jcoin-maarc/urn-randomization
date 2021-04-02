API Access
==========

Urn Randomization app may be accessed via a web-based API, permitting it to be
integrated into existing platforms. Authentication is handled via a user-specific API
key provided by the system administrator. It is critical that this key be
stored and used in a secure manner.

The API has 3 endpoints, as described below.

.. autoflask:: urand_gui.app:app
   :endpoints: api_get_config, api_get_participants, api_randomize_participant