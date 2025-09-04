package protocol

import (
	"encoding/binary"
	"fmt"
	"io"
	"net"

	"github.com/7574-sistemas-distribuidos/docker-compose-init/client/bets/models"
)

func SendBetsBatch(conn net.Conn, bets []*models.Bet) error {
	message := buildBatchMessage(bets)

	if len(message) > MaxMessageSize {
		return fmt.Errorf("batch too large: %d bytes", len(message))
	}

	header := make([]byte, HeaderSize)
	header[0] = HeaderTypeBetBatch
	binary.BigEndian.PutUint16(header[1:3], uint16(len(message)))

	fmt.Printf("Sending message size: %.2f KB\n", float64(len(message))/1024)

	if err := writeFull(conn, header); err != nil {
		return fmt.Errorf("send header: %w", err)
	}

	if err := writeFull(conn, message); err != nil {
		return fmt.Errorf("send body: %w", err)
	}

	return nil
}

// Send all bets were sent notification
func SendFinishNotification(conn net.Conn) error {
	header := make([]byte, HeaderSize)
	header[0] = HeaderTypeFinishNotify
	binary.BigEndian.PutUint16(header[1:3], EmptySizeBody)

	if err := writeFull(conn, header); err != nil {
		return fmt.Errorf("send finish notification: %w", err)
	}

	return nil
}

// Request winners to server
func SendWinnersQuery(conn net.Conn, agency string) error {
	message := []byte(agency)

	header := make([]byte, HeaderSize)
	header[0] = HeaderTypeWinnersQuery
	binary.BigEndian.PutUint16(header[1:3], uint16(len(message)))

	if err := writeFull(conn, header); err != nil {
		return fmt.Errorf("send winners query header: %w", err)
	}

	if err := writeFull(conn, message); err != nil {
		return fmt.Errorf("send winners query body: %w", err)
	}

	return nil
}

func ReceiveWinnersList(conn net.Conn) ([]string, error) {
	header := make([]byte, HeaderSize)
	if err := readData(conn, header); err != nil {
		return nil, fmt.Errorf("read winners list header: %w", err)
	}

	msgType := header[0]
	msgLength := binary.BigEndian.Uint16(header[1:3])

	if msgType != HeaderTypeWinnersList {
		return nil, fmt.Errorf("unexpected message type: %d, expected winners list", msgType)
	}

	if msgLength == 0 {
		return []string{}, nil
	}

	message := make([]byte, msgLength)
	if err := readData(conn, message); err != nil {
		return nil, fmt.Errorf("read winners list body: %w", err)
	}

	var winners []string
	for i := 0; i+LengthDNI <= len(message); i += LengthDNI {
		winners = append(winners, string(message[i:i+LengthDNI]))
	}
	return winners, nil
}

func buildBatchMessage(bets []*models.Bet) []byte {
	var batchMessage []byte

	for i, bet := range bets {
		if i > 0 {
			batchMessage = append(batchMessage, BetSeparator)
		}
		betMessage := buildSingleBetMessage(bet)
		batchMessage = append(batchMessage, betMessage...)
	}
	batchMessage = append(batchMessage, FieldEndMarker)
	return batchMessage
}

func buildSingleBetMessage(bet *models.Bet) []byte {
	fields := []string{
		bet.Agency,
		bet.FirstName,
		bet.LastName,
		bet.Document,
		bet.Birthdate,
		bet.Number,
	}

	var message []byte
	for i, field := range fields {
		if i > 0 {
			message = append(message, FieldSeparator)
		}
		message = append(message, []byte(field)...)
	}

	return message
}

func WaitForBatchConfirmation(conn net.Conn) error {
	header := make([]byte, HeaderSize)
	if err := readData(conn, header); err != nil {
		return fmt.Errorf("read confirmation header: %w", err)
	}

	msgType := header[0]

	switch msgType {
	case HeaderTypeConfirm:
		return nil
	case HeaderTypeFailure:
		return fmt.Errorf("batch processing failed")
	default:
		return fmt.Errorf("unexpected message type: %d", msgType)
	}
}

// Reads all bytes from the connection preventing short reads
func readData(r io.Reader, buf []byte) error {
	_, err := io.ReadFull(r, buf)
	return err
}

// Writes all bytes to the connection preventing short writes
func writeFull(conn net.Conn, data []byte) error {
	total := 0
	for total < len(data) {
		n, err := conn.Write(data[total:])
		if err != nil {
			return err
		}
		total += n
	}
	return nil
}
