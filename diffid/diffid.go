package main

import (
	"fmt"
	"io"
	"os"

	"github.com/google/go-containerregistry/pkg/v1/tarball"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Printf("Usage: %s <path/to/layer.tar.gz>\n", os.Args[0])
		os.Exit(1)
		return
	}

	filePath := os.Args[1]

	layer, err := tarball.LayerFromOpener(func() (io.ReadCloser, error) {
		return os.Open(filePath)
	})
	if err != nil {
		panic(fmt.Errorf("error creating layer from opener: %w", err))
	}

	diffID, err := layer.DiffID()
	if err != nil {
		panic(fmt.Errorf("error calculating DiffID: %w", err))
	}

	fmt.Printf("%s\n", diffID.String())
}

