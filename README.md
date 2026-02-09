Flow Lock: Behavioral API DefenseFlow Lock is an intelligent, middleware-based security engine designed to protect APIs from sophisticated bots that bypass traditional rate limiters. By analyzing the entropy and velocity of incoming traffic, Flow Lock distinguishes between human "chaos" and robotic "precision."
Key Features
Behavioral Fingerprinting: Beyond IP counting, we analyze the statistical variance of request intervals to detect "mechanical" rhythm.
Zero-Trust Dashboard: A high-tech, 3D Glassmorphic command center for real-time threat monitoring and quarantine management.
Self-Healing Quarantine: Automatically blocks malicious IPs with an RFC-compliant 403 Forbidden and Retry-After protocol.
High Performance: Built with FastAPI and in-memory deques, ensuring $O(1)$ space complexity and sub-millisecond overhead.
Signature-less Detection: No need for massive blacklists—threats are identified by their actions in real-time.
The Tech Stack
Language: Python 3.9+Framework: FastAPI (Asynchronous Middleware)Server: UvicornAnalytics: Python statistics & collections 
Frontend: HTML5, CSS3 (Glassmorphism & 3D Transforms)
How It Works:
The Heuristic EngineFlow Lock evaluates traffic through a multi-factor scoring pipeline:
Velocity Sensor (RPM): Tracks the number of requests per minute.
Entropy Sensor (Variance): Measures the randomness of timing. Humans are naturally stochastic (high variance), while bots are deterministic (low variance).Risk Aggregator: Combines metrics into a 0-100% Risk Score.$$Risk = f(RPM) + f(Variance^{-1})
Installation & SetupClone the repositoryBashgit clone https://github.com/[your-username]/flow-lock.git
cd flow-lock
Install dependenciesBashpip install fastapi uvicorn requests
Run the Secure ServerBashpython api_abuse_detection.py
Access the DashboardOpen your browser and navigate to: http://127.0.0.1:8000/status🧪 Demonstration1. The Human TestNavigate to http://127.0.0.1:8000/data and refresh the page manually with varying intervals. Check the dashboard to see a Low Risk Score.2. The Bot AttackRun the included simulation script:Bashpython attacker.py
Watch the Dashboard as the IP is instantly flagged and moved to the Quarantine Zone once the risk hits 100%.🗺️ Roadmap[ ] Redis integration for distributed horizontal scaling.[ ] JWT and Browser Fingerprinting to prevent IP-spoofing bypass.[ ] AI-driven adaptive thresholding based on historical traffic patterns.[ ] Honeypot redirection for advanced threat intelligence gathering.

Author
Dev Kohli
@devkohli1129-hash
