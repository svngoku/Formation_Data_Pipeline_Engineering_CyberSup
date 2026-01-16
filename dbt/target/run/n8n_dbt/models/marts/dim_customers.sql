
  
    

  create  table "neondb"."analytics"."dim_customers__dbt_tmp"
  
  
    as
  
  (
    select
    customer_id,
    first_name,
    last_name,
    email,
    created_at
from "neondb"."analytics"."stg_customers"
  );
  