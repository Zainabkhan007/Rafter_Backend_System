"""
Chart Generation for PDF Reports
Uses matplotlib to generate charts as base64 images for embedding in PDFs
"""

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
import base64
from io import BytesIO
import numpy as np


class ChartGenerator:
    """Generate charts as base64 images for PDF embedding"""

    # Brand colors
    BRAND_PRIMARY = '#009c5b'
    BRAND_SECONDARY = '#9ad983'
    BRAND_COLORS = ['#009c5b', '#9ad983', '#4CAF50', '#8BC34A', '#CDDC39', '#7CB342']

    def __init__(self):
        # Set default style
        plt.style.use('seaborn-v0_8-darkgrid')
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica']

    def generate_bar_chart(self, data, title, xlabel, ylabel, horizontal=False):
        """
        Generate bar chart
        data: list of dicts with 'label' and 'value' keys
        """
        if not data:
            return self._create_no_data_chart(title)

        fig, ax = plt.subplots(figsize=(10, 6))

        labels = [item['label'] for item in data]
        values = [item['value'] for item in data]

        if horizontal:
            bars = ax.barh(labels, values, color=self.BRAND_PRIMARY)
            ax.set_xlabel(ylabel)
            ax.set_ylabel(xlabel)
        else:
            bars = ax.bar(labels, values, color=self.BRAND_PRIMARY)
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            plt.xticks(rotation=45, ha='right')

        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)

        # Add value labels on bars
        for i, (bar, value) in enumerate(zip(bars, values)):
            if horizontal:
                ax.text(value, i, f' {value}', va='center', fontsize=10)
            else:
                ax.text(i, value, f'{value}', ha='center', va='bottom', fontsize=10)

        plt.tight_layout()
        return self._to_base64(fig)

    def generate_line_chart(self, data, title, xlabel, ylabel, multiple_series=False):
        """
        Generate line chart for trends
        data: list of dicts with 'x' and 'y' keys, or dict of series for multiple lines
        """
        if not data:
            return self._create_no_data_chart(title)

        fig, ax = plt.subplots(figsize=(10, 6))

        if multiple_series:
            # Multiple lines
            for i, (series_name, series_data) in enumerate(data.items()):
                x_values = [item['x'] for item in series_data]
                y_values = [item['y'] for item in series_data]
                color = self.BRAND_COLORS[i % len(self.BRAND_COLORS)]
                ax.plot(x_values, y_values, color=color, linewidth=2, marker='o', label=series_name)
            ax.legend(loc='best')
        else:
            # Single line
            x_values = [item['x'] for item in data]
            y_values = [item['y'] for item in data]
            ax.plot(x_values, y_values, color=self.BRAND_PRIMARY, linewidth=2, marker='o', markersize=6)

        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        return self._to_base64(fig)

    def generate_pie_chart(self, data, title, show_legend=True):
        """
        Generate pie chart
        data: list of dicts with 'label' and 'value' keys
        """
        if not data:
            return self._create_no_data_chart(title)

        # Filter out zero or invalid values and check if any data remains
        valid_data = [item for item in data if item.get('value', 0) > 0]

        if not valid_data or sum(item['value'] for item in valid_data) == 0:
            return self._create_no_data_chart(title)

        fig, ax = plt.subplots(figsize=(8, 8))

        labels = [item['label'] for item in valid_data]
        sizes = [item['value'] for item in valid_data]

        # Ensure sizes are valid numbers
        import math
        sizes = [s if not (math.isnan(s) or math.isinf(s)) else 0 for s in sizes]

        # If all sizes are 0 after filtering, show no data chart
        if sum(sizes) == 0:
            plt.close(fig)
            return self._create_no_data_chart(title)

        colors = self.BRAND_COLORS[:len(valid_data)]

        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels if not show_legend else None,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            textprops={'fontsize': 11}
        )

        # Make percentage text bold
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')

        if show_legend:
            ax.legend(labels, loc='center left', bbox_to_anchor=(1, 0, 0.5, 1))

        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)

        plt.tight_layout()
        return self._to_base64(fig)

    def generate_stacked_bar_chart(self, data, title, xlabel, ylabel):
        """
        Generate stacked bar chart
        data: dict with category as key and dict of subcategories as values
        """
        if not data:
            return self._create_no_data_chart(title)

        fig, ax = plt.subplots(figsize=(10, 6))

        categories = list(data.keys())
        subcategories = list(list(data.values())[0].keys())

        # Prepare data for stacking
        values = {subcat: [] for subcat in subcategories}
        for category in categories:
            for subcat in subcategories:
                values[subcat].append(data[category].get(subcat, 0))

        # Create stacked bars
        bottom = np.zeros(len(categories))
        for i, subcat in enumerate(subcategories):
            color = self.BRAND_COLORS[i % len(self.BRAND_COLORS)]
            ax.bar(categories, values[subcat], bottom=bottom, label=subcat, color=color)
            bottom += np.array(values[subcat])

        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.legend(loc='upper left')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        return self._to_base64(fig)

    def generate_grouped_bar_chart(self, data, title, xlabel, ylabel):
        """
        Generate grouped bar chart
        data: dict with group names as keys and dict of values as values
        """
        if not data:
            return self._create_no_data_chart(title)

        fig, ax = plt.subplots(figsize=(10, 6))

        groups = list(data.keys())
        categories = list(list(data.values())[0].keys())

        x = np.arange(len(groups))
        width = 0.8 / len(categories)

        for i, category in enumerate(categories):
            values = [data[group][category] for group in groups]
            offset = (i - len(categories) / 2) * width + width / 2
            color = self.BRAND_COLORS[i % len(self.BRAND_COLORS)]
            ax.bar(x + offset, values, width, label=category, color=color)

        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(groups)
        ax.legend(loc='upper left')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        return self._to_base64(fig)

    def generate_heatmap(self, data, title, xlabel, ylabel, row_labels, col_labels):
        """
        Generate heatmap
        data: 2D array of values
        """
        if not data or not any(data):
            return self._create_no_data_chart(title)

        fig, ax = plt.subplots(figsize=(10, 8))

        im = ax.imshow(data, cmap='Greens', aspect='auto')

        # Set ticks and labels
        ax.set_xticks(np.arange(len(col_labels)))
        ax.set_yticks(np.arange(len(row_labels)))
        ax.set_xticklabels(col_labels)
        ax.set_yticklabels(row_labels)

        # Rotate the tick labels
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right', rotation_mode='anchor')

        # Add text annotations
        for i in range(len(row_labels)):
            for j in range(len(col_labels)):
                text = ax.text(j, i, data[i][j], ha='center', va='center', color='black')

        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)

        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Value', rotation=270, labelpad=20)

        plt.tight_layout()
        return self._to_base64(fig)

    def generate_trend_arrow_chart(self, current_value, previous_value, label):
        """
        Generate a simple trend indicator with arrow
        """
        fig, ax = plt.subplots(figsize=(6, 4))

        change = current_value - previous_value
        percent_change = (change / previous_value * 100) if previous_value != 0 else 0

        # Determine color and arrow
        if change > 0:
            color = '#4CAF50'  # Green
            arrow = '↑'
        elif change < 0:
            color = '#F44336'  # Red
            arrow = '↓'
        else:
            color = '#9E9E9E'  # Grey
            arrow = '→'

        ax.text(0.5, 0.6, f"{current_value:,.0f}", ha='center', va='center',
                fontsize=36, fontweight='bold', color=color)

        ax.text(0.5, 0.35, f"{arrow} {abs(percent_change):.1f}%", ha='center', va='center',
                fontsize=24, color=color)

        ax.text(0.5, 0.15, label, ha='center', va='center',
                fontsize=14, color='#666')

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        plt.tight_layout()
        return self._to_base64(fig)

    def _create_no_data_chart(self, title):
        """Create a placeholder chart when no data available"""
        fig, ax = plt.subplots(figsize=(8, 6))

        ax.text(0.5, 0.5, 'No Data Available', ha='center', va='center',
                fontsize=24, color='#999')
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.axis('off')

        plt.tight_layout()
        return self._to_base64(fig)

    def _to_base64(self, fig):
        """Convert matplotlib figure to base64 string with high quality (300 DPI)"""
        buffer = BytesIO()
        # Use 300 DPI for professional print-quality charts
        fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none', pad_inches=0.1)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close(fig)
        return f"data:image/png;base64,{image_base64}"
