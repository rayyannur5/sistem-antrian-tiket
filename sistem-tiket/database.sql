-- Drop tables if they exist
DROP TABLE IF EXISTS TicketHold;
DROP TABLE IF EXISTS Ticket;
DROP TABLE IF EXISTS User;

-- Create the User table
CREATE TABLE User (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL
);

-- Create the Ticket table
CREATE TABLE Ticket (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    stock INT NOT NULL
);

-- Create the TicketHold table
CREATE TABLE TicketHold (
    id VARCHAR(36) PRIMARY KEY,
    expires_at DATETIME NOT NULL,
    user_id INT NOT NULL,
    ticket_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES User(id) ON DELETE CASCADE,
    FOREIGN KEY (ticket_id) REFERENCES Ticket(id) ON DELETE CASCADE
);


CREATE TABLE Transaction (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    ticket_id INT NOT NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES User(id) ON DELETE CASCADE,
    FOREIGN KEY (ticket_id) REFERENCES Ticket(id) ON DELETE CASCADE
)

-- Insert default users
INSERT INTO User (name, email) VALUES
('Alice', 'alice@example.com'),
('Bob', 'bob@example.com');

-- Insert default tickets
INSERT INTO Ticket (name, stock) VALUES
('Concert A', 100),
('Concert B', 50),
('Concert C', 75);
