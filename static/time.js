function toNumber(value, defaultValue = 0) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : defaultValue;
}

export function calculateTimeBreakdown({
    processes = [],
    manualSetup = 0,
    manualTool = 0,
    manualIdle = 0,
    manualMisc = 0,
} = {}) {
    const machiningTime = processes.reduce((sum, process) => {
        const result = process?.result || {};
        return sum + toNumber(result.total_time_minutes ?? result.time);
    }, 0);

    const breakdown = {
        machiningTime,
        idleTime: toNumber(manualIdle),
        setupTime: toNumber(manualSetup),
        toolTime: toNumber(manualTool),
        miscTime: toNumber(manualMisc),
    };

    breakdown.totalTime = (
        breakdown.machiningTime +
        breakdown.idleTime +
        breakdown.setupTime +
        breakdown.toolTime +
        breakdown.miscTime
    );

    return breakdown;
}
