package utils

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/7574-sistemas-distribuidos/docker-compose-init/client/bets/models"
	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// Reads bets from a CSV file with a fixed quantity determined from the environment variable MAX_AMOUNT
func BetsFromFile() ([]*models.Bet, error) {
	cliID := os.Getenv("CLI_ID")
	if cliID == "" {
		return nil, fmt.Errorf("CLI_ID environment variable not set")
	}

	log.Infof("action: read_bets | result: in_progress | client_id: %v", cliID)

	batchSize, err := getBatchSize()
	if err != nil {
		return nil, err
	}

	log.Infof("action: batch_size_set | result: success | client_id: %v | count: %d", cliID, batchSize)

	csvPath := filepath.Join("/data/", "agency-"+cliID+".csv")
	bets, err := readBetsFromCSV(csvPath, batchSize, cliID)
	if err != nil {
		return nil, fmt.Errorf("read bets from CSV: %w", err)
	}

	return bets, nil
}

// Reads and validates the MAX_AMOUNT environment variable
func getBatchSize() (int, error) {
	batchSizeStr := os.Getenv("MAX_AMOUNT")
	if batchSizeStr == "" {
		return 1, nil
	}

	batchSize, err := strconv.Atoi(batchSizeStr)
	if err != nil {
		return 0, fmt.Errorf("invalid MAX_AMOUNT: %v", batchSizeStr)
	}
	if batchSize <= 0 {
		return 0, fmt.Errorf("MAX_AMOUNT must be positive, got: %d", batchSize)
	}

	return batchSize, nil
}

// Reads bets from a CSV file using bufio for line-by-line reading
func readBetsFromCSV(filePath string, maxBets int, agency string) ([]*models.Bet, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, fmt.Errorf("open file: %w", err)
	}
	defer file.Close()

	var bets []*models.Bet
	scanner := bufio.NewScanner(file)
	lineNumber := 0

	for scanner.Scan() && len(bets) < maxBets {
		lineNumber++
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}

		bet, err := parseBetFromCSVLine(line, lineNumber, agency)
		if err != nil {
			log.Warningf("action: parse_line | result: skip | line: %d | error: %v", lineNumber, err)
			continue
		}

		bets = append(bets, bet)
	}

	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("scan file: %w", err)
	}

	return bets, nil
}

// Parses a single CSV line into a Bet model
func parseBetFromCSVLine(line string, lineNumber int, agency string) (*models.Bet, error) {
	fields := strings.Split(line, ",")
	if len(fields) != 5 {
		return nil, fmt.Errorf("wrong number of fields, expected 5, got %d", len(fields))
	}

	for i := range fields {
		fields[i] = strings.TrimSpace(fields[i])
	}

	requiredFields := []string{fields[0], fields[1], fields[2], fields[3], fields[4]}
	for i, field := range requiredFields {
		if field == "" {
			return nil, fmt.Errorf("empty required field at position %d", i)
		}
	}

	return &models.Bet{
		Agency:    agency,
		FirstName: fields[0],
		LastName:  fields[1],
		Document:  fields[2],
		Birthdate: fields[3],
		Number:    fields[4],
	}, nil
}
