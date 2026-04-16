function toNumber(value, defaultValue = 0) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : defaultValue;
}

export function calculateCostBreakdown({
    materialCost = 0,
    laborRatePerHour = 0,
    toolCostPerUse = 0,
    miscCost = 0,
    timeBreakdown = {},
    overheadRate = 0.4,
} = {}) {
    const laborRatePerMinute = toNumber(laborRatePerHour) / 60;
    const setupIdleTime = toNumber(timeBreakdown.setupTime) + toNumber(timeBreakdown.idleTime);
    const setupIdleCost = setupIdleTime * laborRatePerMinute;
    const machiningCost = toNumber(timeBreakdown.machiningTime) * laborRatePerMinute;
    const toolingCost = toNumber(toolCostPerUse) + (toNumber(timeBreakdown.toolTime) * laborRatePerMinute);
    const totalRawCost = (
        toNumber(materialCost) +
        setupIdleCost +
        machiningCost +
        toolingCost +
        toNumber(miscCost)
    );
    const overheadCost = totalRawCost * toNumber(overheadRate, 0.4);

    return {
        materialCost: toNumber(materialCost),
        laborRatePerHour: toNumber(laborRatePerHour),
        setupIdleTime,
        setupIdleCost,
        machiningCost,
        toolingCost,
        miscCost: toNumber(miscCost),
        totalRawCost,
        overheadCost,
        finalCost: totalRawCost + overheadCost,
    };
}
