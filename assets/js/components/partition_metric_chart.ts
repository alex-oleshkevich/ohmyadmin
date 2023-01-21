import { html, LitElement, PropertyValues } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import Chart from 'chart.js/auto';

@customElement('x-partition-metric-chart')
export class PartitionMetricChart extends LitElement {
    @property() series: string = '';
    @property() label: string = '';
    @property() color: string = '#3b82f6';
    // @property({ type: Boolean }) ticks: boolean = false;
    // @property({ type: Boolean }) grid: boolean = false;
    // @property({ type: Boolean }) legend: boolean = false;
    // @property({ attribute: 'backgroundColor' }) backgroundColor: string = 'rgb(239 246 255)';

    getDataSet() {
        const template = document.querySelector<HTMLScriptElement>(`#${ this.series }`);
        return JSON.parse(template!.innerText);
    }

    protected firstUpdated(_changedProperties: PropertyValues) {
        const series = this.getDataSet();
        const context = this.querySelector<HTMLCanvasElement>('canvas:first-child');
        new Chart(context!, {
            type: 'doughnut',
            data: {
                labels: Object.keys(series),
                datasets: [{
                    data: Object.values<{ color: string, value: number }>(series).map(v => v.value),
                    backgroundColor: Object.values<{ color: string, value: number }>(series).map(v => v.color),
                }]
            },
            options: {
                cutout: '75%',
                maintainAspectRatio: true,
                interaction: { mode: 'index', intersect: false },
                layout: {
                    autoPadding: false,
                    padding: { bottom: -8, left: -4, right: 0, top: 4 },
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
                    legend: { display: false },
                }
            }
        });
    }

    protected render(): unknown {
        return html`
            <div style="height: 80px">
                <canvas></canvas>
            </div>`;
    }

    protected createRenderRoot(): Element | ShadowRoot {
        return this;
    }
}
