#!/usr/bin/env node
declare class QuackMCPServer {
    private server;
    private db;
    private loadedTables;
    constructor();
    private setupToolHandlers;
    loadCSV(args: any): Promise<{
        content: {
            type: string;
            text: string;
        }[];
    }>;
    private queryCSV;
    private describeTable;
    private listTables;
    private analyzeCSV;
    optimizeExpenses(args: any): Promise<{
        content: {
            type: string;
            text: string;
        }[];
    }>;
    private inspectTableSchema;
    private getColumnTypeIcon;
    private formatSampleData;
    private executeQuery;
    private safeStringify;
    private generateExpenseOptimizationReport;
    private formatOptimizationReport;
    run(): Promise<void>;
}
export { QuackMCPServer };
