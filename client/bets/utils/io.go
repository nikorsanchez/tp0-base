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

type CSVScanner struct {
	scanner    *bufio.Scanner
	file       *os.File
	lineNumber int
	eof        bool
	agency     string
}

// Creates a new scanner to read the CSV file
func NewCSVScanner(file *os.File) *CSVScanner {
	cliID := os.Getenv("CLI_ID")
	return &CSVScanner{
		scanner: bufio.NewScanner(file),
		file:    file,
		agency:  cliID,
		eof:     false,
	}
}

func (s *CSVScanner) ReadBatch(batchSize int) ([]*models.Bet, error) {
	var bets []*models.Bet

	for len(bets) < batchSize {
		if !s.scanner.Scan() {
			s.eof = true
			break
		}

		s.lineNumber++
		line := strings.TrimSpace(s.scanner.Text())
		if line == "" {
			continue
		}

		bet, err := parseBetFromCSVLine(line, s.agency)
		if err != nil {
			log.Warningf("action: parse_line | result: skip | line: %d | error: %v", s.lineNumber, err)
			continue
		}

		bets = append(bets, bet)
	}

	if err := s.scanner.Err(); err != nil {
		return nil, fmt.Errorf("scan file: %w", err)
	}

	return bets, nil
}

// Indicates if the end of the file has been reached
func (s *CSVScanner) IsEOF() bool {
	return s.eof
}

func GetCSVFilePath(cliID string) string {
	return filepath.Join("/data/", "agency-"+cliID+".csv")
}

// Reads and validates the MAX_AMOUNT environment variable
func GetBatchSize() (int, error) {
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

func BetsFromFile() ([]*models.Bet, error) {
	cliID := os.Getenv("CLI_ID")
	if cliID == "" {
		return nil, fmt.Errorf("CLI_ID environment variable not set")
	}

	batchSize, err := GetBatchSize()
	if err != nil {
		return nil, err
	}

	csvPath := GetCSVFilePath(cliID)
	file, err := os.Open(csvPath)
	if err != nil {
		return nil, fmt.Errorf("open file: %w", err)
	}
	defer file.Close()

	scanner := NewCSVScanner(file)
	return scanner.ReadBatch(batchSize)
}

// Parses line into a Bet
func parseBetFromCSVLine(line string, agency string) (*models.Bet, error) {
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