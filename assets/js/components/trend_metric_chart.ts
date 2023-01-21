import { html, LitElement, PropertyValues } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import Chart from 'chart.js/auto';

type ChartSeries = [string, number][];

@customElement('x-trend-metric-chart')
export class LineChart extends LitElement {
    @property() series: string = '';
    @property() label: string = '';
    @property() color: string = '#3b82f6';
    @property({ type: Boolean }) ticks: boolean = false;
    @property({ type: Boolean }) grid: boolean = false;
    @property({ type: Boolean }) legend: boolean = false;
    @property({ attribute: 'backgroundColor' }) backgroundColor: string = 'rgb(239 246 255)';

    getDataSet(): ChartSeries {
        const template = document.querySelector<HTMLScriptElement>(`#${ this.series }`);
        return JSON.parse(template!.innerText);
    }

    protected firstUpdated(_changedProperties: PropertyValues) {
        const series = this.getDataSet();
        const context = this.querySelector<HTMLCanvasElement>('canvas:first-child');
        new Chart(context!, {
            type: 'line',
            data: {
                labels: series.map((v: [string, number]) => v[0]),
                datasets: [
                    {
                        label: this.label,
                        tension: 0.1,
                        fill: true,
                        borderColor: this.color,
                        backgroundColor: this.backgroundColor,
                        data: series.map((v: [string, number]) => v[1]),
                    }
                ]
            },
            options: {
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                layout: {
                    autoPadding: false,
                    padding: { bottom: -8, left: -4, right: 0, top: 4 },
                },
                scales: {
                    x: {
                        title: { display: false, padding: 0 },
                        border: { display: false },
                        ticks: { display: this.ticks, padding: 0 },
                        grid: { display: this.grid },
                    },
                    y: {
                        title: { display: false, padding: 0 },
                        border: { display: false },
                        ticks: { display: this.ticks, padding: 0 },
                        grid: { display: this.grid }
                    },
                },
                plugins: {
                    tooltip: {
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
                    legend: { display: this.legend },
                }
            }
        });
    }

    protected render(): unknown {
        return html`
            <div style="height: 72px">
                <canvas></canvas>
            </div>`;
    }

    protected createRenderRoot(): Element | ShadowRoot {
        return this;
    }
}
