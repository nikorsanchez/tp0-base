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
	LoopAmount    int
	LoopPeriod    time.Duration
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
	time.Sleep(1 * time.Second)
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

	bets, err := utils.BetsFromFile()
	if err != nil {
		log.Errorf("action: read_bets | result: fail | client_id: %v | error: %v", c.config.ID, err)
		c.GracefulShutdown()
		return
	}

	log.Infof("action: read_bets | result: success | client_id: %v | bets_count: %d", c.config.ID, len(bets))

	log.Infof("action: sending_batch | result: in_progress | client_id: %v | bets_count: %d", c.config.ID, len(bets))

	err = protocol.SendBetsBatch(c.conn, bets)
	if err != nil {
		log.Errorf("action: send_batch | result: fail | client_id: %v | error: %v", c.config.ID, err)
		c.conn.Close()
		c.GracefulShutdown()
		return
	}

	err = protocol.WaitForBatchConfirmation(c.conn)
	c.conn.Close()

	if err != nil {
		log.Errorf("action: batch_de_apuestas_enviadas | result: fail | client_id: %v | error: %v",
			c.config.ID, err)
		c.GracefulShutdown()
		return
	}

	log.Infof("action: batch_de_apuestas_enviadas | result: success")

	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
	c.GracefulShutdown()
}
