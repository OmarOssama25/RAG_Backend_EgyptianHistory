const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const axios = require('axios'); // New import for HTTP requests

// Flask model server URL
const MODEL_SERVER_URL = process.env.MODEL_SERVER_URL || 'http://localhost:5050';

// Track indexing status
let indexingStatus = {
  isIndexing: false,
  progress: 0,
  error: null,
  message: null,
  lastIndexed: null,
  currentFile: null
};

exports.uploadPdf = (req, res) => {
  try {
    console.log("Upload request received");
    console.log("File details:", req.file);
    
    if (!req.file) {
      return res.status(400).json({ success: false, message: 'No file uploaded' });
    }
    
    console.log("File successfully saved to:", req.file.path);
    
    // Check if there's existing metadata for this file and remove it
    // to ensure it shows up as unindexed
    const baseFileName = req.file.filename.replace('.pdf', '');
    const metadataPath = path.join(__dirname, '../../vector_store', `${baseFileName}_metadata.json`);
    
    if (fs.existsSync(metadataPath)) {
      try {
        fs.unlinkSync(metadataPath);
        console.log(`Deleted existing metadata file for ${baseFileName} to mark as unindexed`);
      } catch (err) {
        console.warn(`Warning: Could not delete metadata file ${metadataPath}:`, err.message);
      }
    }
    
    res.status(200).json({ 
      success: true, 
      message: 'File uploaded successfully and ready for indexing', 
      filename: req.file.filename,
      path: req.file.path,
      requiresIndexing: true
    });
  } catch (error) {
    console.error('Error uploading file:', error);
    res.status(500).json({ success: false, message: 'Error uploading file', error: error.message });
  }
};

// Index the document
exports.indexDocument = (req, res) => {
  try {
    if (indexingStatus.isIndexing) {
      return res.status(409).json({ 
        success: false, 
        message: 'Indexing already in progress', 
        progress: indexingStatus.progress 
      });
    }

    // Get filename from request body instead of hardcoding
    const { filename } = req.body;
    
    // Validate that filename was provided
    if (!filename) {
      return res.status(400).json({
        success: false,
        message: 'Filename is required'
      });
    }
    
    const pdfPath = path.join(__dirname, '../../data', filename);
    
    if (!fs.existsSync(pdfPath)) {
      return res.status(404).json({ 
        success: false, 
        message: `PDF file ${filename} not found. Please upload the file first.` 
      });
    }

    // Update indexing status with current file info
    indexingStatus = {
      isIndexing: true,
      progress: 0,
      error: null,
      message: null,
      lastIndexed: null,
      currentFile: filename
    };

    console.log(`Starting indexing process for ${filename}`);

    // Run the Python indexer script
    const pythonProcess = spawn('python', [
      path.join(__dirname, '../../rag/indexer.py'),
      pdfPath
    ]);

    pythonProcess.stdout.on('data', (data) => {
      const output = data.toString().trim();
      console.log('Indexer output:', output);
      
      // Try to parse progress updates
      try {
        if (output.includes('progress:')) {
          const progressMatch = output.match(/progress: (\d+)/);
          if (progressMatch && progressMatch[1]) {
            indexingStatus.progress = parseInt(progressMatch[1]);
          }
        } else if (output.includes('completed')) {
          // This is a completion message
          indexingStatus.message = output;
        }
      } catch (e) {
        console.error('Error parsing progress:', e);
      }
    });

    pythonProcess.stderr.on('data', (data) => {
      const output = data.toString();
      console.log(`Indexer stderr output: ${output}`);
      
      // Determine if this is an actual error or just an info message
      if (output.includes('ERROR') || output.includes('Error:')) {
        indexingStatus.error = output;
      } else if (output.includes('completed') || output.includes('INFO')) {
        // This is likely an info message printed to stderr
        indexingStatus.message = output;
      }
    });

    pythonProcess.on('close', (code) => {
      console.log(`Indexing process for ${filename} exited with code ${code}`);
      
      if (code === 0) {
        indexingStatus.progress = 100;
        indexingStatus.lastIndexed = new Date().toISOString();
        
        // REMOVE THIS BLOCK - DO NOT CREATE METADATA FILE HERE
        // The Python indexer script should create the proper metadata file with chunks
        
        // Set success message
        if (!indexingStatus.message) {
          indexingStatus.message = `Indexing of ${filename} completed successfully`;
        }
        
        // Clear any error that might have been set incorrectly
        if (indexingStatus.error && indexingStatus.error.includes('INFO') && indexingStatus.error.includes('completed')) {
          const message = indexingStatus.error;
          indexingStatus.error = null;
          indexingStatus.message = message;
        }
      } else {
        if (!indexingStatus.error) {
          indexingStatus.error = `Process exited with code ${code}`;
        }
      }
      
      // Mark indexing as complete regardless of outcome
      indexingStatus.isIndexing = false;
    });

    res.status(202).json({ 
      success: true, 
      message: `Indexing started for ${filename}`, 
      status: indexingStatus 
    });
  } catch (error) {
    console.error('Error starting indexing process:', error);
    indexingStatus.isIndexing = false;
    indexingStatus.error = error.message;
    res.status(500).json({ 
      success: false, 
      message: 'Error starting indexing process', 
      error: error.message 
    });
  }
};


// Check indexing status
exports.getIndexingStatus = (req, res) => {
  res.status(200).json({ 
    success: true,
    status: indexingStatus
  });
};

// Query the RAG system using the Flask model server
exports.queryRag = async (req, res) => {
  try {
    // Accept either query or question parameter
    const queryText = req.body.question || req.body.query;
    
    console.log(`RAG query received: "${queryText}"`);
    
    if (!queryText) {
      return res.status(400).json({ 
        success: false, 
        message: 'Question is required' 
      });
    }

    // [existing validation code remains the same]

    // Call the Flask model server API
    try {
      console.log(`Sending query to model server: ${MODEL_SERVER_URL}/query`);
      const modelResponse = await axios.post(`${MODEL_SERVER_URL}/query`, {
        query: queryText,
        top_k: 5
      });
      
      console.log('Model server response received');
      
      // Extract the answer text from any response format
      let rawData = modelResponse.data;
      let plainTextAnswer = '';
      
      // Case 1: If it's a JSON string, parse it
      if (typeof rawData === 'string' && (rawData.startsWith('{') || rawData.startsWith('['))) {
        try {
          const parsed = JSON.parse(rawData);
          plainTextAnswer = parsed.answer || '';
        } catch (e) {
          plainTextAnswer = rawData;
        }
      } 
      // Case 2: If it's already an object with answer property
      else if (typeof rawData === 'object' && rawData.answer) {
        plainTextAnswer = rawData.answer;
      }
      // Case 3: If it has response property instead
      else if (typeof rawData === 'object' && rawData.response) {
        plainTextAnswer = rawData.response;
      }
      // Case 4: Fallback to string conversion
      else {
        plainTextAnswer = String(rawData);
      }
      
      // Force text/plain content type to prevent JSON formatting
      res.setHeader('Content-Type', 'text/plain');
      res.status(200).send(plainTextAnswer);
    } catch (error) {
      console.error('Error calling model server:', error.message);
      
      // Send plain text error
      res.setHeader('Content-Type', 'text/plain');
      res.status(500).send('Error generating response from model server');
    }
  } catch (error) {
    console.error('Error in queryRag function:', error);
    
    // Send plain text error
    res.setHeader('Content-Type', 'text/plain');
    res.status(500).send('Error processing your question');
  }
};


// Get indexing status
exports.getStatus = (req, res) => {
  // Create a clean copy of the status for the response
  const statusResponse = {
    isIndexing: indexingStatus.isIndexing,
    progress: indexingStatus.progress,
    message: indexingStatus.message,
    error: indexingStatus.error,
    lastIndexed: indexingStatus.lastIndexed
  };
  
  res.status(200).json({
    success: true,
    status: statusResponse
  });
};

exports.getDocuments = (req, res) => {
  try {
    const dataDir = path.join(__dirname, '../../data');
    const vectorStoreDir = path.join(__dirname, '../../vector_store');
    
    // Ensure data directory exists
    if (!fs.existsSync(dataDir)) {
      console.log('Data directory does not exist');
      return res.status(200).json({ documents: [] });
    }
    
    // Get all PDF files from data directory
    const pdfFiles = fs.readdirSync(dataDir)
      .filter(file => file.toLowerCase().endsWith('.pdf'));
    console.log("PDF files found in data directory:", pdfFiles);
    
    // Create a set of indexed document names (without extension)
    const indexedDocsSet = new Set();
    
    // Check if vector store directory exists before trying to read it
    if (fs.existsSync(vectorStoreDir)) {
      // Look specifically for metadata files with the exact naming pattern
      const metadataFiles = fs.readdirSync(vectorStoreDir)
        .filter(file => file.endsWith('_metadata.json'));
      
      metadataFiles.forEach(file => {
        const docName = file.replace('_metadata.json', '');
        indexedDocsSet.add(docName.toLowerCase());
      });
      
      console.log("Indexed documents set:", Array.from(indexedDocsSet));
    } else {
      console.log("Vector store directory does not exist yet - no indexed documents");
    }
    
    // Map PDF files to document objects
    const documents = pdfFiles.map(file => {
      const fileName = file.replace('.pdf', '');
      const fullPath = path.join(dataDir, file);
      const stats = fs.statSync(fullPath);
      
      // Check if document is indexed - use strict check with exact pattern matching
      const isIndexed = indexedDocsSet.has(fileName.toLowerCase());
      
      return {
        id: fileName,
        filename: file,
        originalName: file,
        path: fullPath,
        uploadDate: stats.mtime,
        indexed: isIndexed, // This will now be false for new uploads
        size: stats.size,
      };
    });
    
    console.log("Found documents:", documents);
    
    res.status(200).json({ documents });
  } catch (error) {
    console.error('Error getting documents:', error);
    res.status(500).json({ 
      error: 'Failed to retrieve documents',
      details: error.message 
    });
  }
};