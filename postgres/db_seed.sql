INSERT INTO customers VALUES
('C1','Alice','2024-01-02'),('C2','Bob','2024-02-11'),('C3','Chloé','2024-03-05');

INSERT INTO categories VALUES
('CAT1','Electronics'),('CAT2','Books');

INSERT INTO products VALUES
('P1','Wireless Mouse',29.99,'CAT1'),
('P2','USB-C Hub',49.00,'CAT1'),
('P3','Graph Databases Book',39.00,'CAT2'),
('P4','Mechanical Keyboard',89.00,'CAT1');

INSERT INTO orders VALUES
('O1','C1','2024-04-01T10:15:00Z'),
('O2','C2','2024-04-02T12:30:00Z'),
('O3','C1','2024-04-05T08:05:00Z');

INSERT INTO order_items VALUES
('O1','P1',1),('O1','P2',1),('O2','P3',1),('O3','P4',1),('O3','P2',1);

INSERT INTO events VALUES
('E1','C1','P3','view','2024-04-01T09:00:00Z'),
('E2','C1','P3','click','2024-04-01T09:01:00Z'),
('E3','C3','P1','view','2024-04-03T16:20:00Z'),
('E4','C2','P2','view','2024-04-03T12:00:00Z'),
('E5','C2','P4','add_to_cart','2024-04-03T12:10:00Z');