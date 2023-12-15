import { html, LitElement } from 'lit';
import { customElement, property, query } from 'lit/decorators.js';
import Chart from 'chart.js/auto';
import { resolveColor } from '../utils';

type Slice = {
    color: string,
    label: string,
    value: number,
}


@customElement('o-metric-trend')
export class TrendMetricElement extends LitElement {
    @property()
    series: string = '';

    @property({ attribute: 'label' })
    label: string = '';

    @property()
    color: string = '';

    @property({ attribute: 'bg-color' })
    backgroundColor: string = '';

    @property({ type: Boolean, attribute: 'ticks' })
    showTicks: boolean = false;

    @property({ type: Boolean, attribute: 'grid' })
    showGrid: boolean = false;

    @property({ type: Boolean, attribute: 'tooltip' })
    showTooltip: boolean = false;

    @query('canvas')
    canvasEl!: HTMLCanvasElement;
    chart: Chart | null = null;

    override render() {
        return html`
            <section>
                <canvas style="height: 80px"></canvas>
            </section>`;
    }

    getSeries(): Slice[] {
        return JSON.parse(document.querySelector<HTMLScriptElement>(this.series)?.innerText!);
    }

    protected override firstUpdated() {
        const series = this.getSeries();
        this.chart = new Chart(this.canvasEl!, {
            type: 'line',
            data: {
                labels: series.map(v => v.label),
                datasets: [
                    {
                        tension: 0.1,
                        fill: true,
                        borderColor: resolveColor(this.color),
                        backgroundColor: resolveColor(this.backgroundColor),
                        data: series.map(v => v.value),
                    }
                ]
            },
            options: {
                maintainAspectRatio: false,
                interaction: { mode: 'point', intersect: false },
                layout: {
                    autoPadding: false,
                    padding: 0,
                },
                scales: {
                    x: {
                        title: { display: false, padding: 0 },
                        border: { display: false },
                        ticks: { display: this.showTicks, padding: 0 },
                        grid: {
                            display: this.showGrid,
                            drawTicks: this.showTicks,
                            color: resolveColor('--o-border-color')
                        },
                    },
                    y: {
                        title: { display: false, padding: 0 },
                        border: { display: false },
                        ticks: { display: this.showTicks, padding: 0 },
                        grid: {
                            display: this.showGrid,
                            drawTicks: this.showTicks,
                            color: resolveColor('--o-border-color')
                        }
                    },
                },
                plugins: {
                    tooltip: {
                        enabled: this.showTooltip,
                        padding: 12,
                        titleColor: 'black',
                        titleFont: { size: 16 },
                        titleSpacing: 4,
                        titleMarginBottom: 8,
                        bodyColor: 'black',
                        footerColor: 'black',
                        bodyFont: { size: 16 },
                        borderColor: 'rgb(203 213 225)',
                        borderWidth: 1,
                        backgroundColor: 'white',
                        bodySpacing: 4,
                    },
                    legend: { display: false },
                }
            }
        });
    }

}
