INSERT INTO public.user_security_level (
    name,
    note,
    token_max_live_count,
    token_max_lifetime,
    token_min_creation_interval,
    token_max_jobs,
    token_max_budget,
    token_max_rate,
    login_max_interval
) VALUES (
    'DEFAULT',
    'Default security level for users',
    10,
    3600,
    60,  
    50000,
    10000,
    100,  
    3600  
)
ON CONFLICT (name) DO NOTHING;  -- avoid duplicates
INSERT INTO "user" (identity,note, email, affiliation, association, security_level, blocked, block_reason, secret_hash, force_secret_reset) VALUES    ('di75bus', '','Burak.Mete@lrz.de', 'LRZ QCT', 'LDAP','DEFAULT','f','','','f');
INSERT INTO public.token VALUES ('4c97628d2210bccff16e2047d3301261cbc23c33aae6aa7be860e66da4901f74',        'di75bus',      'text', '2024-06-13 13:30:05.397733',   '2026-08-13 13:30:05.397733',     false,  'no', NULL,'2024-08-13 13:30:05.397733', 10000, 1000);
INSERT INTO public.target_specification (name, note, specification_type, minimum_qubits, quantum_technology, resource_name) VALUES ('QExa20'::text, 'Mock'::text, 'resource'::text, '1'::text, ' '::text, 'QExa20'::text) returning name;
INSERT INTO user_group VALUES ('test_user', '', 'di75bus', 1);
INSERT INTO public.budget VALUES ('temp_budget',    'text', 'di75bus',      1000); 
INSERT INTO users_in_user_groups VALUES ( 'di75bus', 'test_user');
INSERT INTO user_groups_in_budgets VALUES ('temp_budget', 'test_user');