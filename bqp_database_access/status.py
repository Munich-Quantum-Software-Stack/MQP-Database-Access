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

"""MQP-Database-Access Status module"""
import random
from datetime import datetime

from ._database import open_database


def _weighted_sample_without_replacement(population, weights, k, rng=random):
    v = [rng.random() ** (1 / w) for w in weights]
    order = sorted(range(len(population)), key=lambda i: v[i])
    return [population[i] for i in order[-k:]]


def fetch_current_announcements() -> tuple["Announcement"]:  # type: ignore
    """Fetch all mandatory announcements."""

    quantum_db = open_database()

    announcements = quantum_db.Announcement.select(
        lambda a: a.start_time < datetime.now() and a.end_time > datetime.now()
    )

    return tuple(announcements)


def get_random_pointers(count: int) -> list["Pointer"]:  # type: ignore
    """Return a weighted random selection of currently active pointers."""

    quantum_db = open_database()

    pointers = list(
        quantum_db.Pointer.select(
            lambda p: p.start_time < datetime.now() and p.end_time > datetime.now()
        )
    )

    weights = [pointer.weight for pointer in pointers]

    return _weighted_sample_without_replacement(pointers, weights, count)
