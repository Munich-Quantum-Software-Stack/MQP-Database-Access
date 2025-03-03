CREATE OR REPLACE PROCEDURE InsertTimeSlot(
  start_time TIMESTAMP,
  end_time TIMESTAMP,
  resource_name TEXT,
  user_ids TEXT[] DEFAULT '{}',
  user_groups TEXT[] DEFAULT '{}',
  note TEXT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
  v_time_slot_id INT;
  v_user_id TEXT;
  v_user_group TEXT;
BEGIN
  -- Validate input parameters
  IF start_time IS NULL OR end_time IS NULL OR resource_name IS NULL THEN
    RAISE EXCEPTION 'start_time, end_time and resource_name cannot be NULL.';
  END IF;

  IF start_time >= end_time THEN
    RAISE EXCEPTION 'start_time must be before end_time.';
  END IF;

  -- Check resource exists
  IF NOT EXISTS (SELECT 1 FROM resource WHERE name = resource_name) THEN
    RAISE EXCEPTION 'Resource % does not exist.', resource_name;
  END IF;

  -- Check user exists
  IF array_length(user_ids, 1) > 0 THEN
    FOREACH v_user_id IN ARRAY user_ids LOOP
      IF NOT EXISTS (SELECT 1 FROM "user" WHERE identity = v_user_id) THEN
        RAISE EXCEPTION 'User % does not exist.', v_user_id;
      END IF;
    END LOOP;
  END IF;

  -- Check user group exists
  IF array_length(user_groups, 1) > 0 THEN
    FOREACH v_user_group IN ARRAY user_groups LOOP
      IF NOT EXISTS (SELECT 1 FROM user_group WHERE name = v_user_group) THEN
        RAISE EXCEPTION 'User group % does not exist.', v_user_group;
      END IF;
    END LOOP;
  END IF;

  -- Insert time slot
  INSERT INTO time_slots (start_time, end_time, resource_name, note)
  VALUES (start_time, end_time, resource_name, note)
  RETURNING id INTO v_time_slot_id;

  IF array_length(user_ids, 1) > 0 THEN
    INSERT INTO users_in_time_slots (timeslots, "user")
    SELECT v_time_slot_id, uid
    FROM unnest(user_ids) AS t(uid);
  END IF;

  IF array_length(user_groups, 1) > 0 THEN
    INSERT INTO user_groups_in_time_slots (timeslots, usergroup)
    SELECT v_time_slot_id, ugroup
    FROM unnest(user_groups) AS t(ugroup);
  END IF;

END;
$$;
