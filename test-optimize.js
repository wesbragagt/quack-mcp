#!/usr/bin/env node

import { QuackMCPServer } from './dist/index.js';
import Database from 'duckdb';

// Create a simple test
async function testOptimizeExpenses() {
  try {
    // Create a test server instance
    const server = new QuackMCPServer();
    
    // Load the credit card data
    await server.loadCSV({
      file_path: './credit-card.csv',
      table_name: 'credit_card'
    });
    
    // Test the optimize expenses functionality
    const result = await server.optimizeExpenses({
      table_name: 'credit_card'
    });
    
    console.log('Expense Optimization Report:');
    console.log('============================');
    console.log(result.content[0].text);
    
  } catch (error) {
    console.error('Test failed:', error);
  }
}

testOptimizeExpenses();