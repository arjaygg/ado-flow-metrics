/**
 * Export & Collaboration Module for Flow Metrics Dashboard
 * 
 * Provides comprehensive export capabilities including PDF reports, Excel exports,
 * dashboard sharing, team collaboration tools, and data exchange features.
 */

class ExportCollaboration {
    constructor() {
        this.exportFormats = new Map();
        this.collaborationSettings = new Map();
        this.shareLinks = new Map();
        this.exportHistory = [];
        this.maxHistorySize = 50;
        
        // Export format configurations
        this.initializeExportFormats();
        
        // Collaboration features
        this.collaborationEnabled = true;
        this.shareableBaseUrl = window.location.origin + window.location.pathname;
        
        console.log('Export & Collaboration module initialized');
    }

    /**
     * Initialize export format configurations
     */
    initializeExportFormats() {
        this.exportFormats.set('pdf', {
            name: 'PDF Report',
            description: 'Comprehensive PDF report with charts and metrics',
            mimeType: 'application/pdf',
            extension: '.pdf',
            supportsCharts: true,
            supportsData: true,
            supportsCustomization: true
        });

        this.exportFormats.set('excel', {
            name: 'Excel Spreadsheet',
            description: 'Raw data and calculated metrics in Excel format',
            mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            extension: '.xlsx',
            supportsCharts: false,
            supportsData: true,
            supportsCustomization: false
        });

        this.exportFormats.set('csv', {
            name: 'CSV Data',
            description: 'Comma-separated values for data analysis',
            mimeType: 'text/csv',
            extension: '.csv',
            supportsCharts: false,
            supportsData: true,
            supportsCustomization: false
        });

        this.exportFormats.set('json', {
            name: 'JSON Data',
            description: 'Structured data in JSON format',
            mimeType: 'application/json',
            extension: '.json',
            supportsCharts: false,
            supportsData: true,
            supportsCustomization: false
        });

        this.exportFormats.set('png', {
            name: 'PNG Image',
            description: 'Dashboard screenshot in PNG format',
            mimeType: 'image/png',
            extension: '.png',
            supportsCharts: true,
            supportsData: false,
            supportsCustomization: false
        });
    }

    /**
     * Export dashboard data in specified format
     * @param {string} format - Export format (pdf, excel, csv, json, png)
     * @param {Object} data - Dashboard data to export
     * @param {Object} options - Export options
     * @returns {Promise<Blob>} Exported data as blob
     */
    async exportData(format, data, options = {}) {
        const formatConfig = this.exportFormats.get(format);
        if (!formatConfig) {
            throw new Error(`Unsupported export format: ${format}`);
        }

        const exportOptions = {
            title: options.title || 'Flow Metrics Dashboard Report',
            subtitle: options.subtitle || `Generated on ${new Date().toLocaleDateString()}`,
            includeCharts: options.includeCharts !== false,
            includeData: options.includeData !== false,
            dateRange: options.dateRange || 'All time',
            ...options
        };

        let exportedData;

        switch (format) {
            case 'pdf':
                exportedData = await this.exportToPDF(data, exportOptions);
                break;
            case 'excel':
                exportedData = await this.exportToExcel(data, exportOptions);
                break;
            case 'csv':
                exportedData = await this.exportToCSV(data, exportOptions);
                break;
            case 'json':
                exportedData = await this.exportToJSON(data, exportOptions);
                break;
            case 'png':
                exportedData = await this.exportToPNG(exportOptions);
                break;
            default:
                throw new Error(`Export handler not implemented for format: ${format}`);
        }

        // Add to export history
        this.addToExportHistory(format, exportOptions);

        return exportedData;
    }

    /**
     * Export dashboard to PDF format
     * @param {Object} data - Dashboard data
     * @param {Object} options - Export options
     * @returns {Promise<Blob>} PDF blob
     */
    async exportToPDF(data, options) {
        // Use jsPDF library for PDF generation (would need to be included)
        if (typeof window.jsPDF === 'undefined') {
            throw new Error('jsPDF library not available. Please include jsPDF in your project.');
        }

        const { jsPDF } = window.jsPDF;
        const doc = new jsPDF();

        // PDF configuration
        const pageWidth = doc.internal.pageSize.width;
        const pageHeight = doc.internal.pageSize.height;
        const margin = 20;
        let yPosition = margin;

        // Helper function to add new page if needed
        const checkPageBreak = (neededHeight) => {
            if (yPosition + neededHeight > pageHeight - margin) {
                doc.addPage();
                yPosition = margin;
            }
        };

        // Title
        doc.setFontSize(20);
        doc.setFont(undefined, 'bold');
        doc.text(options.title, margin, yPosition);
        yPosition += 15;

        // Subtitle
        doc.setFontSize(12);
        doc.setFont(undefined, 'normal');
        doc.text(options.subtitle, margin, yPosition);
        yPosition += 10;

        // Date range
        doc.setFontSize(10);
        doc.text(`Date Range: ${options.dateRange}`, margin, yPosition);
        yPosition += 20;

        // Key Metrics Section
        checkPageBreak(40);
        doc.setFontSize(16);
        doc.setFont(undefined, 'bold');
        doc.text('Key Metrics', margin, yPosition);
        yPosition += 15;

        doc.setFontSize(10);
        doc.setFont(undefined, 'normal');

        // Add metrics table
        const metrics = this.extractKeyMetrics(data);
        const metricsData = [
            ['Metric', 'Average', 'Median', 'Trend'],
            ['Lead Time', `${metrics.leadTime.average} days`, `${metrics.leadTime.median} days`, metrics.leadTime.trend],
            ['Cycle Time', `${metrics.cycleTime.average} days`, `${metrics.cycleTime.median} days`, metrics.cycleTime.trend],
            ['Throughput', `${metrics.throughput.value} items/period`, '-', metrics.throughput.trend],
            ['WIP', `${metrics.wip.value} items`, '-', metrics.wip.trend]
        ];

        this.addTableToPDF(doc, metricsData, margin, yPosition, pageWidth - 2 * margin);
        yPosition += (metricsData.length * 8) + 20;

        // Team Performance Section
        if (data.team_metrics && Object.keys(data.team_metrics).length > 0) {
            checkPageBreak(60);
            doc.setFontSize(16);
            doc.setFont(undefined, 'bold');
            doc.text('Team Performance', margin, yPosition);
            yPosition += 15;

            const teamData = [['Team', 'Lead Time', 'Cycle Time', 'Completed Items']];
            Object.entries(data.team_metrics).forEach(([team, metrics]) => {
                teamData.push([
                    team,
                    `${(metrics.average_lead_time || 0).toFixed(1)} days`,
                    `${(metrics.average_cycle_time || 0).toFixed(1)} days`,
                    `${metrics.completed_items || 0} items`
                ]);
            });

            this.addTableToPDF(doc, teamData, margin, yPosition, pageWidth - 2 * margin);
            yPosition += (teamData.length * 8) + 20;
        }

        // Historical Data Section
        if (data.historical_data && data.historical_data.length > 0) {
            checkPageBreak(40);
            doc.setFontSize(16);
            doc.setFont(undefined, 'bold');
            doc.text('Recent Work Items', margin, yPosition);
            yPosition += 15;

            // Show last 10 items
            const recentItems = data.historical_data.slice(-10);
            const itemsData = [['ID', 'Type', 'Lead Time', 'Cycle Time', 'Resolved Date']];
            
            recentItems.forEach(item => {
                itemsData.push([
                    item.id || 'N/A',
                    item.workItemType || 'N/A',
                    `${(item.leadTime || 0).toFixed(1)} days`,
                    `${(item.cycleTime || 0).toFixed(1)} days`,
                    item.resolvedDate || 'N/A'
                ]);
            });

            this.addTableToPDF(doc, itemsData, margin, yPosition, pageWidth - 2 * margin);
            yPosition += (itemsData.length * 8) + 20;
        }

        // Footer
        const totalPages = doc.internal.getNumberOfPages();
        for (let i = 1; i <= totalPages; i++) {
            doc.setPage(i);
            doc.setFontSize(8);
            doc.text(
                `Page ${i} of ${totalPages} - Generated by Flow Metrics Dashboard`,
                margin,
                pageHeight - 10
            );
        }

        return new Blob([doc.output('blob')], { type: 'application/pdf' });
    }

    /**
     * Export dashboard to Excel format
     * @param {Object} data - Dashboard data
     * @param {Object} options - Export options
     * @returns {Promise<Blob>} Excel blob
     */
    async exportToExcel(data, options) {
        // Use SheetJS library for Excel generation (would need to be included)
        if (typeof XLSX === 'undefined') {
            throw new Error('SheetJS library not available. Please include XLSX in your project.');
        }

        const workbook = XLSX.utils.book_new();

        // Summary sheet
        const summaryData = this.prepareSummaryDataForExport(data);
        const summaryWS = XLSX.utils.aoa_to_sheet(summaryData);
        XLSX.utils.book_append_sheet(workbook, summaryWS, 'Summary');

        // Historical data sheet
        if (data.historical_data && data.historical_data.length > 0) {
            const historicalData = this.prepareHistoricalDataForExport(data.historical_data);
            const historicalWS = XLSX.utils.json_to_sheet(historicalData);
            XLSX.utils.book_append_sheet(workbook, historicalWS, 'Historical Data');
        }

        // Team metrics sheet
        if (data.team_metrics && Object.keys(data.team_metrics).length > 0) {
            const teamData = this.prepareTeamDataForExport(data.team_metrics);
            const teamWS = XLSX.utils.json_to_sheet(teamData);
            XLSX.utils.book_append_sheet(workbook, teamWS, 'Team Metrics');
        }

        // Generate Excel file
        const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
        return new Blob([excelBuffer], { 
            type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
        });
    }

    /**
     * Export dashboard to CSV format
     * @param {Object} data - Dashboard data
     * @param {Object} options - Export options
     * @returns {Promise<Blob>} CSV blob
     */
    async exportToCSV(data, options) {
        let csvContent = '';

        // Header
        csvContent += `"Flow Metrics Dashboard Export"\n`;
        csvContent += `"${options.title}"\n`;
        csvContent += `"Generated: ${new Date().toISOString()}"\n`;
        csvContent += `"Date Range: ${options.dateRange}"\n\n`;

        // Historical data
        if (data.historical_data && data.historical_data.length > 0) {
            csvContent += `"Historical Data"\n`;
            
            // Headers
            const headers = ['ID', 'Work Item Type', 'Lead Time (days)', 'Cycle Time (days)', 'Resolved Date'];
            csvContent += headers.map(h => `"${h}"`).join(',') + '\n';
            
            // Data rows
            data.historical_data.forEach(item => {
                const row = [
                    item.id || '',
                    item.workItemType || '',
                    item.leadTime || '',
                    item.cycleTime || '',
                    item.resolvedDate || ''
                ];
                csvContent += row.map(cell => `"${cell}"`).join(',') + '\n';
            });
        }

        return new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    }

    /**
     * Export dashboard to JSON format
     * @param {Object} data - Dashboard data
     * @param {Object} options - Export options
     * @returns {Promise<Blob>} JSON blob
     */
    async exportToJSON(data, options) {
        const exportData = {
            metadata: {
                title: options.title,
                subtitle: options.subtitle,
                exportDate: new Date().toISOString(),
                dateRange: options.dateRange,
                version: '1.0'
            },
            data: data
        };

        const jsonString = JSON.stringify(exportData, null, 2);
        return new Blob([jsonString], { type: 'application/json;charset=utf-8;' });
    }

    /**
     * Export dashboard to PNG image
     * @param {Object} options - Export options
     * @returns {Promise<Blob>} PNG blob
     */
    async exportToPNG(options) {
        // Use html2canvas library for screenshot generation
        if (typeof html2canvas === 'undefined') {
            throw new Error('html2canvas library not available. Please include html2canvas in your project.');
        }

        // Get dashboard container
        const dashboardElement = document.querySelector('.container-fluid') || document.body;
        
        const canvas = await html2canvas(dashboardElement, {
            height: dashboardElement.scrollHeight,
            width: dashboardElement.scrollWidth,
            scrollX: 0,
            scrollY: 0,
            useCORS: true,
            scale: 1
        });

        return new Promise((resolve) => {
            canvas.toBlob(resolve, 'image/png');
        });
    }

    /**
     * Generate shareable dashboard link
     * @param {Object} dashboardState - Current dashboard state
     * @param {Object} options - Sharing options
     * @returns {string} Shareable URL
     */
    generateShareableLink(dashboardState, options = {}) {
        const shareId = this.generateShareId();
        const shareData = {
            id: shareId,
            title: options.title || 'Flow Metrics Dashboard',
            description: options.description || 'Shared dashboard view',
            createdAt: new Date().toISOString(),
            expiresAt: options.expiresAt || this.getDefaultExpirationDate(),
            allowEdit: options.allowEdit || false,
            password: options.password || null,
            state: dashboardState
        };

        // Store share data (in a real implementation, this would be stored on a server)
        this.shareLinks.set(shareId, shareData);
        this.storeShareLinkLocally(shareData);

        const shareUrl = `${this.shareableBaseUrl}?share=${shareId}`;
        return shareUrl;
    }

    /**
     * Load shared dashboard state
     * @param {string} shareId - Share identifier
     * @returns {Object|null} Shared dashboard state
     */
    loadSharedDashboard(shareId) {
        // First check local storage
        const shareData = this.getShareLinkFromLocal(shareId);
        if (!shareData) {
            return null;
        }

        // Check if share link has expired
        if (new Date() > new Date(shareData.expiresAt)) {
            this.removeShareLink(shareId);
            return null;
        }

        return shareData;
    }

    /**
     * Create collaboration room for team sharing
     * @param {Object} options - Room options
     * @returns {Object} Room information
     */
    createCollaborationRoom(options = {}) {
        const roomId = this.generateRoomId();
        const roomData = {
            id: roomId,
            name: options.name || 'Flow Metrics Collaboration Room',
            description: options.description || 'Team collaboration space',
            createdAt: new Date().toISOString(),
            createdBy: options.createdBy || 'Anonymous',
            participants: options.participants || [],
            settings: {
                allowEdit: options.allowEdit !== false,
                allowExport: options.allowExport !== false,
                autoSync: options.autoSync !== false,
                maxParticipants: options.maxParticipants || 10
            }
        };

        this.collaborationSettings.set(roomId, roomData);
        this.storeCollaborationRoomLocally(roomData);

        return roomData;
    }

    /**
     * Join collaboration room
     * @param {string} roomId - Room identifier
     * @param {Object} participant - Participant information
     * @returns {Object|null} Room data if successfully joined
     */
    joinCollaborationRoom(roomId, participant) {
        const roomData = this.getCollaborationRoomFromLocal(roomId);
        if (!roomData) {
            return null;
        }

        // Check participant limit
        if (roomData.participants.length >= roomData.settings.maxParticipants) {
            throw new Error('Collaboration room is full');
        }

        // Add participant
        const participantData = {
            id: participant.id || this.generateParticipantId(),
            name: participant.name || 'Anonymous',
            joinedAt: new Date().toISOString(),
            role: participant.role || 'viewer'
        };

        roomData.participants.push(participantData);
        this.collaborationSettings.set(roomId, roomData);
        this.storeCollaborationRoomLocally(roomData);

        return roomData;
    }

    /**
     * Send collaboration message
     * @param {string} roomId - Room identifier
     * @param {Object} message - Message data
     */
    sendCollaborationMessage(roomId, message) {
        const roomData = this.collaborationSettings.get(roomId);
        if (!roomData) {
            throw new Error('Collaboration room not found');
        }

        const messageData = {
            id: this.generateMessageId(),
            roomId: roomId,
            senderId: message.senderId,
            senderName: message.senderName || 'Anonymous',
            type: message.type || 'text', // text, filter-change, annotation, etc.
            content: message.content,
            timestamp: new Date().toISOString()
        };

        // In a real implementation, this would be sent to other participants
        // via WebSocket or similar real-time communication
        console.log('Collaboration message:', messageData);
        
        // Store message locally for demo purposes
        this.storeCollaborationMessage(messageData);
    }

    /**
     * Download exported file
     * @param {Blob} blob - File blob
     * @param {string} filename - Desired filename
     */
    downloadFile(blob, filename) {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

    /**
     * Get export history
     * @returns {Array} Export history
     */
    getExportHistory() {
        return [...this.exportHistory];
    }

    /**
     * Get available export formats
     * @returns {Array} Available export formats
     */
    getAvailableFormats() {
        return Array.from(this.exportFormats.entries()).map(([key, config]) => ({
            id: key,
            ...config
        }));
    }

    // Helper methods

    extractKeyMetrics(data) {
        return {
            leadTime: {
                average: (data.lead_time?.average_days || 0).toFixed(1),
                median: (data.lead_time?.median_days || 0).toFixed(1),
                trend: '→' // Would be calculated from historical data
            },
            cycleTime: {
                average: (data.cycle_time?.average_days || 0).toFixed(1),
                median: (data.cycle_time?.median_days || 0).toFixed(1),
                trend: '→'
            },
            throughput: {
                value: (data.throughput?.items_per_period || 0).toFixed(1),
                trend: '↑'
            },
            wip: {
                value: data.work_in_progress?.total_wip || 0,
                trend: '↓'
            }
        };
    }

    addTableToPDF(doc, data, x, y, width) {
        const rowHeight = 8;
        const colWidth = width / data[0].length;

        data.forEach((row, rowIndex) => {
            row.forEach((cell, colIndex) => {
                const cellX = x + (colIndex * colWidth);
                const cellY = y + (rowIndex * rowHeight);
                
                // Header row styling
                if (rowIndex === 0) {
                    doc.setFont(undefined, 'bold');
                    doc.setFillColor(240, 240, 240);
                    doc.rect(cellX, cellY - 5, colWidth, rowHeight, 'F');
                } else {
                    doc.setFont(undefined, 'normal');
                }
                
                doc.text(String(cell), cellX + 2, cellY);
            });
        });
    }

    prepareSummaryDataForExport(data) {
        const metrics = this.extractKeyMetrics(data);
        return [
            ['Flow Metrics Dashboard Summary'],
            ['Generated:', new Date().toISOString()],
            [],
            ['Metric', 'Average', 'Median'],
            ['Lead Time (days)', metrics.leadTime.average, metrics.leadTime.median],
            ['Cycle Time (days)', metrics.cycleTime.average, metrics.cycleTime.median],
            ['Throughput (items/period)', metrics.throughput.value, ''],
            ['Work in Progress', metrics.wip.value, '']
        ];
    }

    prepareHistoricalDataForExport(historicalData) {
        return historicalData.map(item => ({
            ID: item.id || '',
            'Work Item Type': item.workItemType || '',
            'Lead Time (days)': item.leadTime || '',
            'Cycle Time (days)': item.cycleTime || '',
            'Resolved Date': item.resolvedDate || '',
            Priority: item.priority || '',
            Assignee: item.assignee || '',
            State: item.state || ''
        }));
    }

    prepareTeamDataForExport(teamMetrics) {
        return Object.entries(teamMetrics).map(([team, metrics]) => ({
            Team: team,
            'Average Lead Time (days)': (metrics.average_lead_time || 0).toFixed(1),
            'Average Cycle Time (days)': (metrics.average_cycle_time || 0).toFixed(1),
            'Completed Items': metrics.completed_items || 0,
            'Active Items': metrics.active_items || 0
        }));
    }

    addToExportHistory(format, options) {
        const historyEntry = {
            id: this.generateHistoryId(),
            format: format,
            title: options.title,
            timestamp: new Date().toISOString(),
            size: 'Unknown' // Would be calculated from actual file size
        };

        this.exportHistory.unshift(historyEntry);
        
        // Limit history size
        if (this.exportHistory.length > this.maxHistorySize) {
            this.exportHistory = this.exportHistory.slice(0, this.maxHistorySize);
        }

        // Store in localStorage
        this.storeExportHistory();
    }

    generateShareId() {
        return 'share_' + Math.random().toString(36).substr(2, 16) + Date.now().toString(36);
    }

    generateRoomId() {
        return 'room_' + Math.random().toString(36).substr(2, 12) + Date.now().toString(36);
    }

    generateParticipantId() {
        return 'participant_' + Math.random().toString(36).substr(2, 8);
    }

    generateMessageId() {
        return 'msg_' + Math.random().toString(36).substr(2, 12);
    }

    generateHistoryId() {
        return 'export_' + Math.random().toString(36).substr(2, 12);
    }

    getDefaultExpirationDate() {
        const expiry = new Date();
        expiry.setDate(expiry.getDate() + 7); // 7 days default
        return expiry.toISOString();
    }

    storeShareLinkLocally(shareData) {
        try {
            const stored = JSON.parse(localStorage.getItem('flowMetrics_shareLinks') || '{}');
            stored[shareData.id] = shareData;
            localStorage.setItem('flowMetrics_shareLinks', JSON.stringify(stored));
        } catch (error) {
            console.warn('Failed to store share link locally:', error);
        }
    }

    getShareLinkFromLocal(shareId) {
        try {
            const stored = JSON.parse(localStorage.getItem('flowMetrics_shareLinks') || '{}');
            return stored[shareId] || null;
        } catch (error) {
            console.warn('Failed to retrieve share link from local storage:', error);
            return null;
        }
    }

    removeShareLink(shareId) {
        try {
            const stored = JSON.parse(localStorage.getItem('flowMetrics_shareLinks') || '{}');
            delete stored[shareId];
            localStorage.setItem('flowMetrics_shareLinks', JSON.stringify(stored));
            this.shareLinks.delete(shareId);
        } catch (error) {
            console.warn('Failed to remove share link:', error);
        }
    }

    storeCollaborationRoomLocally(roomData) {
        try {
            const stored = JSON.parse(localStorage.getItem('flowMetrics_collaborationRooms') || '{}');
            stored[roomData.id] = roomData;
            localStorage.setItem('flowMetrics_collaborationRooms', JSON.stringify(stored));
        } catch (error) {
            console.warn('Failed to store collaboration room locally:', error);
        }
    }

    getCollaborationRoomFromLocal(roomId) {
        try {
            const stored = JSON.parse(localStorage.getItem('flowMetrics_collaborationRooms') || '{}');
            return stored[roomId] || null;
        } catch (error) {
            console.warn('Failed to retrieve collaboration room from local storage:', error);
            return null;
        }
    }

    storeCollaborationMessage(messageData) {
        try {
            const stored = JSON.parse(localStorage.getItem('flowMetrics_collaborationMessages') || '[]');
            stored.push(messageData);
            
            // Keep only last 100 messages
            if (stored.length > 100) {
                stored.splice(0, stored.length - 100);
            }
            
            localStorage.setItem('flowMetrics_collaborationMessages', JSON.stringify(stored));
        } catch (error) {
            console.warn('Failed to store collaboration message:', error);
        }
    }

    storeExportHistory() {
        try {
            localStorage.setItem('flowMetrics_exportHistory', JSON.stringify(this.exportHistory));
        } catch (error) {
            console.warn('Failed to store export history:', error);
        }
    }

    loadExportHistory() {
        try {
            const stored = localStorage.getItem('flowMetrics_exportHistory');
            if (stored) {
                this.exportHistory = JSON.parse(stored);
            }
        } catch (error) {
            console.warn('Failed to load export history:', error);
        }
    }

    /**
     * Initialize the module
     */
    init() {
        this.loadExportHistory();
        console.log('Export & Collaboration module ready');
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ExportCollaboration;
}