CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE wallet_user (
    customer_xid text PRIMARY KEY,
	token text
);

CREATE TABLE wallet_user_info (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL PRIMARY KEY,
    owned_by uuid NOT NULL,
    status character varying(50) NOT NULL,
	enabled_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
	balance integer not null
);

CREATE TABLE wallet_user_transactions (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    reference_id uuid NOT NULL PRIMARY KEY,
    status character varying(50) NOT NULL,
	owned_by uuid NOT NULL,
	transaction_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
	amount integer not null,
	transaction_type character varying(100) NOT NULL
);