-- This is pseudocode, to be put into an actual parameterized script later

CREATE USER $user_name PASSWORD $password;

GRANT USAGE ON SCHEMA $schema TO $user_name;
GRANT SELECT ON ALL TABLES IN SCHEMA $schema1to $user_name;