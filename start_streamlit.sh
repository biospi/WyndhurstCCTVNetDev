#!/bin/bash
# Navigate to your project directory
cd /home/fo18103/PycharmProjects/WhyndhurstVideoTransfer || exit

# Give the network a few seconds to come up (optional)
sleep 10

# Run Streamlit using the virtual environment's Python
/home/fo18103/PycharmProjects/WhyndhurstVideoTransfer/.venv/bin/python -m streamlit run frontend.py --server.port 8501

/home/fo18103/PycharmProjects/WhyndhurstVideoTransfer/.venv/bin/python update_front_end.py