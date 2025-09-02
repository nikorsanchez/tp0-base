package common

func (c *Client) handleGetBatchSizeError(err error) {
    log.Errorf("action: get_batch_size | result: fail | client_id: %v | error: %v", c.config.ID, err)
    c.GracefulShutdown()
}

func (c *Client) handleGetCSVFilePathError(err error) {
    log.Errorf("action: open_file | result: fail | client_id: %v | error: %v", c.config.ID, err)
		c.GracefulShutdown()
}

func (c *Client) handleBatchReadError(batchNumber int, err error) {
    log.Errorf("action: read_batch | result: fail | client_id: %v | batch: %d | error: %v",
        c.config.ID, batchNumber, err)
    if c.conn != nil {
        c.conn.Close()
    }
    c.GracefulShutdown()
}

func (c *Client) handleSendBetsBatchError(batchNumber int, err error) {
    log.Errorf("action: send_batch | result: fail | client_id: %v | batch: %d | error: %v", 
				c.config.ID, batchNumber, err)
    if c.conn != nil {
        c.conn.Close()
    }
    c.GracefulShutdown()
}

func (c *Client) handleWaitForConfirmationError(batchNumber int, err error) {
    log.Errorf("action: batch_confirmation | result: fail | client_id: %v | batch: %d | error: %v",
				c.config.ID, batchNumber, err)
    if c.conn != nil {
        c.conn.Close()
    }
    c.GracefulShutdown()
}