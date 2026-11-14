export const usd = (value: number) =>
	value.toLocaleString('en-US', { style: 'currency', currency: 'USD' });

export const tokens = (value: number) =>
	value >= 1e6 ? `${(value / 1e6).toFixed(1)}M` : `${Math.round(value / 1e3)}k`;

export const hours = (minutes: number) => {
	const total = Math.round(minutes);
	const whole = Math.floor(total / 60);
	const rest = total % 60;

	return whole ? `${whole} h ${rest} min` : `${rest} min`;
};

export const mm = (value: number) => `${Number(value.toFixed(2))} mm`;

export const points = (value: number) => Number(value.toFixed(1)).toString();

export const percent = (value: number) => `${Number(value.toFixed(1))}%`;

export const ohms = (value: number) =>
	value >= 1000 ? `${Number((value / 1000).toFixed(1))}k` : `${value}`;
