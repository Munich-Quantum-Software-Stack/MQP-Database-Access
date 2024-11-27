# Documentation
## Access restriction
For now, we hardcode access / job-submission rights to our offered quantum hardware via usergroups (database table users_in_user_groups). 
27-11-2024 We added MQP_EDU as a usergroup. In bqp_database_access/resources.py, users in this group cannot submit jobs to any hardware. 