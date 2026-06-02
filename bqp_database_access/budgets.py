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

"""MQP-Database-Access Budget module"""

from ._database import open_database


def create_new_budget(name: str, owner: str, credit_amount: int):
    """Create a new budget entry."""
    raise NotImplementedError


def fetch_budgets_of_identity(identity: str) -> set["Budget", ...]:  # type: ignore
    """Fetch all budgets."""

    quantum_db = open_database()

    user = quantum_db.User.get(identity=identity)

    user_group_budgets = {
        budget for user_group in user.user_groups for budget in user_group.budgets
    }

    return user_group_budgets
