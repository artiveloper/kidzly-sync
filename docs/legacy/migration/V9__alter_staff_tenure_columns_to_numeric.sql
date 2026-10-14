ALTER TABLE daycares
    ALTER COLUMN staff_tenure_under_1y TYPE NUMERIC(5, 1),
    ALTER COLUMN staff_tenure_1y_to_2y TYPE NUMERIC(5, 1),
    ALTER COLUMN staff_tenure_2y_to_4y TYPE NUMERIC(5, 1),
    ALTER COLUMN staff_tenure_4y_to_6y TYPE NUMERIC(5, 1),
    ALTER COLUMN staff_tenure_over_6y  TYPE NUMERIC(5, 1);
