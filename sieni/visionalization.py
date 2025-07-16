from pipa.service.pipashu import PIPAShuData
import json
import numpy as np
import os
import argparse

# Custom JSON encoder to handle NumPy types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process perf data and generate metrics')
    parser.add_argument('--ef_cores', action='store_true', help='Extract core events from cpu_core/event/ or cpu_atom/event/ format')
    parser.add_argument('--workspace_path', default='/home/sieni/Desktop/working_doc/project/Zhou_ZJU/sieni_test/2', help='Path to perf-stat.csv file')
    parser.add_argument('--num_transactions', type=int, default=328452000, help='Number of transactions')
    parser.add_argument('--threads_start', type=int, default=0, help='Start of thread IDs')
    parser.add_argument('--threads_end', type=int, default=12, help='End of thread IDs')
    parser.add_argument('--output', default='pipashu_metrics_pcores.json', help='Output JSON file path')
    parser.add_argument('--perf_stat_path', default='perf-stat.csv', help='Path to perf-stat.csv file')
    
    args = parser.parse_args()

    pipashu = PIPAShuData(
        perf_stat_path=os.path.join(args.workspace_path, args.perf_stat_path),
        sar_path=os.path.join(args.workspace_path, 'sar.txt'),
        perf_record_path=os.path.join(args.workspace_path, 'perf.script'),
    )

    threads = list(range(args.threads_start, args.threads_end))

    output = pipashu.get_metrics(
        num_transactions=args.num_transactions,
        threads=threads,
        ef_cores=args.ef_cores
    )

    # Save output to JSON file
    file_pth = os.path.join(args.workspace_path, args.output)

    with open(file_pth, 'w') as json_file:
        json.dump(output, json_file, indent=4, cls=NumpyEncoder)

    print(f"Metrics saved to {file_pth}")

if __name__ == "__main__":
    main()