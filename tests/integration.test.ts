import { describe, it } from 'node:test';
import assert from 'node:assert';
import { QuackMCPServer } from '../src/index.ts';

describe('QuackMCPServer Integration Tests', () => {
  it('should load and analyze the sample CSV file', async () => {
    const server = new QuackMCPServer();
    
    // Load the actual test data file
    const loadResult = await server.loadCSV({
      file_path: './data/credit-card.csv',
      table_name: 'credit_card_test'
    });

    // Verify successful load
    assert.ok(loadResult.content);
    assert.ok(loadResult.content[0].text.includes('Successfully loaded CSV'));
    assert.ok(loadResult.content[0].text.includes('credit_card_test'));

    // Test querying the loaded data
    const queryResult = await (server as any).queryCSV({
      query: 'SELECT COUNT(*) as total_rows FROM credit_card_test'
    });

    assert.ok(queryResult.content);
    const queryText = queryResult.content[0].text;
    assert.ok(queryText.includes('total_rows'));
    
    // Parse the result to verify we have data
    const resultObj = JSON.parse(queryText);
    assert.ok(Array.isArray(resultObj));
    assert.ok(resultObj.length > 0);
    assert.ok(resultObj[0].total_rows > 0);

    // Test table description
    const describeResult = await (server as any).describeTable({
      table_name: 'credit_card_test'
    });

    assert.ok(describeResult.content);
    assert.ok(describeResult.content[0].text.includes('Schema for table'));

    // Test analysis
    const analysisResult = await (server as any).analyzeCSV({
      table_name: 'credit_card_test'
    });

    assert.ok(analysisResult.content);
    assert.ok(analysisResult.content[0].text.includes('Analysis for table'));

    // Test expense optimization
    const optimizeResult = await server.optimizeExpenses({
      table_name: 'credit_card_test'
    });

    assert.ok(optimizeResult.content);
    assert.ok(optimizeResult.content[0].text.includes('Expense Optimization Report'));
    assert.ok(optimizeResult.content[0].text.includes('Monthly Spending Overview'));

    // Test anomaly detection
    const anomalyResult = await server.detectAnomalies({
      table_name: 'credit_card_test',
      severity_threshold: 'low'
    });

    assert.ok(anomalyResult.content);
    assert.ok(anomalyResult.content[0].text.includes('Anomaly Detection Report'));
  });

  it('should handle table listing correctly', async () => {
    const server = new QuackMCPServer();
    
    // Initially should be empty
    const emptyListResult = await (server as any).listTables();
    assert.ok(emptyListResult.content[0].text.includes('[]'));

    // Load a table
    await server.loadCSV({
      file_path: './data/credit-card.csv',
      table_name: 'test_credit_card'
    });

    // Now should show the loaded table
    const listResult = await (server as any).listTables();
    assert.ok(listResult.content[0].text.includes('test_credit_card'));
    assert.ok(listResult.content[0].text.includes('./data/credit-card.csv'));
  });

  it('should handle errors gracefully', async () => {
    const server = new QuackMCPServer();

    // Test with non-existent file
    await assert.rejects(
      async () => {
        await server.loadCSV({ file_path: './non-existent-file.csv' });
      },
      {
        name: 'McpError'
      }
    );

    // Test query on non-existent table
    await assert.rejects(
      async () => {
        await (server as any).queryCSV({ 
          query: 'SELECT * FROM non_existent_table' 
        });
      },
      {
        name: 'McpError'
      }
    );

    // Test describe on non-existent table
    await assert.rejects(
      async () => {
        await (server as any).describeTable({ 
          table_name: 'non_existent_table' 
        });
      },
      {
        name: 'McpError'
      }
    );
  });
});