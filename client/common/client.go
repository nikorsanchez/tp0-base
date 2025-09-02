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
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-sigChan
		close(c.shutdown)
	}()

	if err := c.createClientSocket(); err != nil {
		c.GracefulShutdown()
		return
	}

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
		bets, err := scanner.ReadBatch(batchSize)
		if err != nil {
			c.handleBatchReadError(batchNumber, err)
			return
		}

		if len(bets) == 0 {
			break
		}

		log.Infof("action: sending_batch | result: in_progress | client_id: %v | batch: %d | bets_count: %d",
			c.config.ID, batchNumber, len(bets))

		err = protocol.SendBetsBatch(c.conn, bets)
		if err != nil {
			c.handleSendBetsBatchError(batchNumber, err)
			return
		}

		err = protocol.WaitForBatchConfirmation(c.conn)
		if err != nil {
			c.handleWaitForConfirmationError(batchNumber, err)
			return
		}

		log.Infof("action: batch_confirmed | result: success | client_id: %v | batch: %d | bets_count: %d",
			c.config.ID, batchNumber, len(bets))

		totalBetsSent += len(bets)
		batchNumber++

		if scanner.IsEOF() {
			break
		}
	}

	log.Infof("action: all_batches_sent | result: success | client_id: %v | total_bets: %d | total_batches: %d",
		c.config.ID, totalBetsSent, batchNumber-1)

	log.Infof("action: finish_notify | result: in_progress | client_id: %v", c.config.ID)

	err = protocol.SendFinishNotification(c.conn)
	if err != nil {
		c.handleWSendFinishNotificationError(err)
		return
	}

	log.Infof("action: finish_notify | result: success | client_id: %v", c.config.ID)

	log.Infof("action: consulta_ganadores | result: in_progress | client_id: %v", c.config.ID)

	err = protocol.SendWinnersQuery(c.conn, c.config.ID)
	if err != nil {
		c.handleSendWinnersQueryError(err)
		return
	}

	log.Infof("action: receive_winners | result: in_progress | client_id: %v", c.config.ID)

	winners, err := protocol.ReceiveWinnersList(c.conn)
	if err != nil {
		c.handleReceiveWinnersError(err)
		return
	}

	log.Infof("action: consulta_ganadores | result: success | cant_ganadores: %d", len(winners))

	if len(winners) > 0 {
		for _, dni := range winners {
			log.Infof("Ganadores para agencia %v: DNI ganador: %v", c.config.ID, dni)
		}
	} else {
		log.Infof("No hay ganadores para agencia %v.", c.config.ID)
	}

	c.conn.Close()
	c.GracefulShutdown()
}
