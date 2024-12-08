import textwrap
from datetime import datetime, timedelta

# The DAG object; we'll need this to instantiate a DAG
from airflow.models.dag import DAG

# Operators; we need this to operate!
from airflow.operators.bash import BashOperator
from airflow.operators.python import BranchPythonOperator

REFERENCE = "hg38.fa.gz"
FASTQ1 = "SRR12799740_1.fastq.gz"
FASTQ2 = "SRR12799740_2.fastq.gz"
with DAG(
    "Bio pipeline",
    default_args={
        "depends_on_past": False,
        "email": ["airflow@example.com"],
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
    template_searchpath="/home/vboxuser/tmp"
    description="Bio task",
    schedule=timedelta(days=1),
    catchup=False,
    tags=["bio"],
) as dag:

    fastqc = BashOperator(
        task_id="fastqc",
        bash_command=f"zcat {FASTQ1} {FASTQ2} | fastqc stdin:fastqc_results",
    )

    index_building = BashOperator(
        task_id="index_building",
	bash_command=f"minimap2 -d ref.mmi {REFERENCE}"
    )

    alignments = BashOperator(
        task_id="alignments_sam",
        bash_command=f"minimap2 -a ref.mmi {FASTQ1} {FASTQ2} > alignment.sam",
    )
    convert_sam_to_bam = BashOperator(
	task_id="convert_sam_to_bam",
        bash_command=f"samtools view -buT {REFERENCE} alignment.sam > alg.bam",
    )

    flagstat = BashOperator(
        task_id="samtools_flagstat",
        bash_command="samtools flagstat \"alg.bam\" > \"samtools_result.txt\"",
    )
    

    parse_result = BashOperator(
        task_id="result parse",
        bash_command="python3 parseMappedResult.py \"samtools_result.txt\" > parse_res.txt",
    )
 
    def choose_branch():
	with open("parse_res.txt", "rt") as f:
		result = f.readline()
        if result == "GOOD":
            return ['good_branch']
        return ['bad_branch']

    branching = BranchPythonOperator(
        task_id='branching',
        python_callable=choose_branch
    )
    dag.doc_md = __doc__
    bad_branch = BashOperator(
        task_id="bad_branch",
        bash_command="echo \":(\"",
    )
    good_branch = BashOperator(
        task_id="good_branch",
        bash_command="echo \"good, go next :)\"",
    )
    sorting = BashOperator(
        task_id="samtools_sort",
        bash_command="samtools sort \"alg.bam\" -o \"alg.sorted.bam\"",
    )
    
    freebayes = BashOperator(
        task_id="freebayes",
        bash_command=f'zcat {REFERENCE} > \"ref.fa\"; freebayes "ref.fa" "alg.sorted.bam" > "sample.vcf"',
    )

    fastqc >> index_building >> alignments >> convert_sam_to_bam >> flagstat >> parse_result >> branching
    branching >> [good_branch, bad_branch]
    good_branch >> sorting >> freebayes
