# ------------------------------------------------------------------------------
# Copyright 2026 Munich Quantum Software Stack Project
#
# Licensed under the Apache License, Version 2.0 with LLVM Exceptions (the
# "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://github.com/Munich-Quantum-Software-Stack/QDMI/blob/develop/LICENSE
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
#
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
# ------------------------------------------------------------------------------

"""MQP-Database-Access Timeslot module"""

from datetime import datetime

from pony.orm import db_session  # type: ignore

from ._database import open_database


@db_session
def check_user_now_in_time_slot_for_resource(userid, resource_name, time_instance):
    """Check if the user is one of the users or user is part of a user_group
    that is in a time slot for the resource."""

    time_instance = datetime.fromisoformat(time_instance)

    quantum_db = open_database()

    user = quantum_db.User.get(identity=userid)
    resource = quantum_db.Resource.get(name=resource_name)

    if not user:
        return False

    if not resource:
        return False

    # pylint: disable=chained-comparison
    time_slots = quantum_db.TimeSlots.select(
        lambda ts: ts.resource_name == resource
        and ts.start_time <= time_instance
        and ts.end_time >= time_instance
    )
    # pylint: enable=chained-comparison

    for time_slot in time_slots:
        if user in time_slot.users:
            return True

        for user_group in user.user_groups:
            if user_group in time_slot.user_groups:
                return True

    return False


@db_session
def get_user_list_in_time_slot_for_resource(resource_name, time_instance):
    """Get the list of users and user_groups in a time slot for the resource."""

    time_instance = datetime.fromisoformat(time_instance)
    quantum_db = open_database()

    resource = quantum_db.Resource.get(name=resource_name)

    if not resource:
        return []
    # pylint: disable=chained-comparison
    time_slots = quantum_db.TimeSlots.select(
        lambda ts: ts.resource_name == resource
        and ts.start_time <= time_instance
        and ts.end_time >= time_instance
    )
    # pylint: enable=chained-comparison

    user_list = []
    for time_slot in time_slots:
        for user in time_slot.users:
            user_list.append(user.identity)

        for user_group in time_slot.user_groups:
            for user in user_group.users:
                user_list.append(user.identity)

    return list(set(user_list))


@db_session
def get_resource_list_in_time_slot(time_instance):
    """Get the list of resources in a time slot."""

    time_instance = datetime.fromisoformat(time_instance)
    quantum_db = open_database()

    # pylint: disable=chained-comparison
    time_slots = quantum_db.TimeSlots.select(
        lambda ts: ts.start_time <= time_instance and ts.end_time >= time_instance
    )
    # pylint: enable=chained-comparison

    resource_list = []
    for time_slot in time_slots:
        resource_list.append(time_slot.resource_name.name)

    return list(set(resource_list))
