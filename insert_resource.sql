INSERT INTO public.resource_security_level (
    name,
    note,
    job_min_interval,
    budget_max_per_job,
    unique_token_required,
    token_max_lifetime
) VALUES (
    'QExa20',
    'Custom security level for QLM resources',
    0,       
    100000,  
    false,   
    3600     
)
ON CONFLICT (name) DO NOTHING;  -- avoid duplicates if it already exists

INSERT INTO public.resource (
    name,
    note,
    maintenance,
    qubits,
    connectivity,
    quantum_technology,
    resource_cost_modifier,
    security_level,
    instructions,
    num_queued_jobs
) VALUES (
    'QExa20',
    'IQM',
    false,
    20,
    'All-to-All',
    'Superconducting',
    1.0,
    'QExa20',
    'RX, CZ',
    0
)
RETURNING name;
