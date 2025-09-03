package common

import (
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/7574-sistemas-distribuidos/docker-compose-init/client/bets/protocol"
	"github.com/7574-sistemas-distribuidos/docker-compose-init/client/bets/utils"
	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
}

// Client Entity that encapsulates how
type Client struct {
	config   ClientConfig
	conn     net.Conn
	shutdown chan struct{}
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config:   config,
		shutdown: make(chan struct{}),
	}
	return client
}

// GracefulShutdown closes the client connection gracefully
func (c *Client) GracefulShutdown() {
	log.Infof("action: client_shutdown | result: in_progress | client_id: %v", c.config.ID)
	time.Sleep(1 * time.Second) // Wait for server logs to be printed for test purposes
	log.Infof("action: exit | result: success | client_id: %v", c.config.ID)
	if c.conn != nil {
		c.conn.Close()
	}
	log.Infof("action: client_shutdown | result: success | client_id: %v", c.config.ID)
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return err
	}
	c.conn = conn
	return nil
}

func (c *Client) StartClient() {
	c.handleSignals()

	if err := c.createClientSocket(); err != nil {
		c.GracefulShutdown()
		return
	}
	defer c.conn.Close()
	defer c.GracefulShutdown()

	batchSize, err := utils.GetBatchSize()
	if err != nil {
		c.handleGetBatchSizeError(err)
		return
	}

	log.Infof("action: batch_size_set | result: success | client_id: %v | count: %d", c.config.ID, batchSize)

	filePath := utils.GetCSVFilePath(c.config.ID)
	file, err := os.Open(filePath)
	if err != nil {
		c.handleGetCSVFilePathError(err)
		return
	}
	defer file.Close()

	scanner := utils.NewCSVScanner(file)
	totalBetsSent := 0
	batchNumber := 1

	for {
		if done, err := c.processBatch(scanner, batchSize, batchNumber, &totalBetsSent); done {
			break
		} else if err != nil {
			return
		}
		batchNumber++
		if scanner.IsEOF() {
			break
		}
	}

	log.Infof("action: all_batches_sent | result: success | client_id: %v | total_bets: %d | total_batches: %d",
		c.config.ID, totalBetsSent, batchNumber-1)
}

func (c *Client) handleSignals() {
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-sigChan
		close(c.shutdown)
	}()
}

func (c *Client) processBatch(scanner *utils.CSVScanner, batchSize, batchNumber int, totalBetsSent *int) (bool, error) {
	bets, err := scanner.ReadBatch(batchSize)
	if err != nil {
		c.handleBatchReadError(batchNumber, err)
		return false, err
	}
	if len(bets) == 0 {
		return true, nil
	}

	log.Infof("action: sending_batch | result: in_progress | client_id: %v | batch: %d | bets_count: %d",
		c.config.ID, batchNumber, len(bets))

	if err := protocol.SendBetsBatch(c.conn, bets); err != nil {
		c.handleSendBetsBatchError(batchNumber, err)
		return false, err
	}

	if err := protocol.WaitForBatchConfirmation(c.conn); err != nil {
		c.handleWaitForConfirmationError(batchNumber, err)
		return false, err
	}

	log.Infof("action: batch_confirmed | result: success | client_id: %v | batch: %d | bets_count: %d",
		c.config.ID, batchNumber, len(bets))

	*totalBetsSent += len(bets)
	return false, nil
}
