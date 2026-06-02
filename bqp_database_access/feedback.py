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

"""MQP-Database-Access Feedback module"""

from datetime import datetime

from ._database import open_database


def create_feedback_for_identity(
    owner: str, rating: int, category: str, note: str
) -> None:
    """Create a feedback record for a user identity."""

    quantum_db = open_database()

    quantum_db.Feedback(
        owner=owner, rating=rating, category=category, date=datetime.now(), note=note
    )

    quantum_db.commit()
