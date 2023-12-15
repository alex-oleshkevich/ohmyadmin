import { html, LitElement } from 'lit';
import { customElement, property, query } from 'lit/decorators.js';
import Chart from 'chart.js/auto';
import { resolveColor } from '../utils';

type Slice = {
    color: string,
    label: string,
    value: number,
}


@customElement('o-metric-partition')
export class PartitionMetricElement extends LitElement {
    @property()
    series: string = '';

    @query('canvas')
    canvasEl!: HTMLCanvasElement;
    chart: Chart | null = null;

    override render() {
        return html`
            <section style="height: 80px">
                <canvas style="max-width: 100px; height: 100%"></canvas>
            </section>`;
    }

    getSeries(): Slice[] {
        return JSON.parse(document.querySelector<HTMLScriptElement>(this.series)?.innerText!);
    }

    protected override firstUpdated() {
        const series = this.getSeries();
        this.chart = new Chart(this.canvasEl!, {
            type: 'doughnut',
            data: {
                labels: series.map(s => s.label),
                datasets: [{
                    data: series.map(s => s.value),
                    backgroundColor: series.map(s => resolveColor(s.color)),
                }]
            },
            options: {
                cutout: '75%',
                maintainAspectRatio: true,
                interaction: { mode: 'index', intersect: false },
                layout: {
                    autoPadding: false,
                    padding: {},
                },
                plugins: {
                    tooltip: {
                        padding: 12,
                        titleColor: 'black',
                        titleFont: { size: 12 },
                        titleSpacing: 4,
                        titleMarginBottom: 8,
                        bodyColor: 'black',
                        footerColor: 'black',
                        bodyFont: { size: 12 },
                        borderColor: 'rgb(203 213 225)',
                        borderWidth: 1,
                        backgroundColor: 'white',
                        bodySpacing: 4,
                    },
                    legend: { display: false },
                },
            }
        });
    }

}
