from ifw.shell.is_shell import ShellCommandDetector


def main():
    detector = ShellCommandDetector()

    # Comprehensive test cases - 100+ new examples
    test_cases = [
        # Valid shell commands - should all be True (40 commands)
        (
            "VALID COMMANDS",
            True,
            [
                "nginx -t",
                "systemctl status apache2",
                "journalctl -f",
                "crontab -e",
                "htop",
                "iotop",
                "netstat -tulpn",
                "ss -tuln",
                "lsof -i :80",
                "uname -a",
                "uptime",
                "free -h",
                "vmstat 1 5",
                "iostat -x 1",
                "sar -u 1 10",
                "tcpdump -i eth0",
                "wireshark",
                "nmap -p 22 192.168.1.1",
                "ping -c 4 google.com",
                "traceroute 8.8.8.8",
                "dig google.com",
                "nslookup github.com",
                "host example.com",
                "wget https://example.com/file.zip",
                "curl -L -o output.html https://httpbin.org/html",
                "rsync -avz /source/ user@host:/dest/",
                "scp -r folder/ user@server:~/",
                "sftp user@hostname",
                "screen -S session_name",
                "tmux new-session -d -s work",
                "nohup python script.py &",
                "jobs -l",
                "bg %1",
                "fg %2",
                "disown %3",
                "at now + 5 minutes",
                "batch",
                "watch -n 2 'ps aux'",
                "strace -p 1234",
                "gdb -p 5678",
            ],
        ),
        # Natural language questions/statements - should all be False (30 examples)
        (
            "NATURAL LANGUAGE",
            False,
            [
                "How can I improve server performance?",
                "What are the benefits of using containers?",
                "Why is my application running slowly?",
                "When should I restart the database?",
                "Where are the configuration files stored?",
                "Who has access to the production server?",
                "Which programming language is better for web development?",
                "Could you recommend a good text editor?",
                "I need help with my deployment pipeline",
                "The server seems to be experiencing issues",
                "My application crashed unexpectedly yesterday",
                "Users are reporting connectivity problems",
                "Performance has degraded since the last update",
                "We need to scale our infrastructure",
                "The database is consuming too much memory",
                "Security vulnerabilities were discovered",
                "Backup procedures need to be reviewed",
                "Monitoring alerts are firing constantly",
                "Load balancing configuration requires optimization",
                "SSL certificates are expiring soon",
                "API response times are unacceptable",
                "Storage capacity is running low",
                "Network latency has increased significantly",
                "Authentication mechanisms need upgrading",
                "Disaster recovery plans are outdated",
                "Compliance requirements have changed",
                "Budget constraints limit our options",
                "Team productivity could be improved",
                "Documentation is incomplete and confusing",
                "Training materials need updating",
            ],
        ),
        # Natural language using command words - should all be False (40 examples)
        (
            "NATURAL LANGUAGE WITH COMMAND WORDS",
            False,
            [
                "grep is my favorite search tool",
                "find can locate files efficiently",
                "cat shows file contents nicely",
                "ls displays directory listings beautifully",
                "cd helps navigate the filesystem",
                "rm removes files permanently from disk",
                "cp creates copies of important files",
                "mv relocates files to different directories",
                "chmod modifies file permissions correctly",
                "chown changes ownership of system files",
                "ps shows all running processes",
                "top displays system resource usage",
                "kill terminates problematic processes gracefully",
                "sudo grants administrative privileges temporarily",
                "ssh connects to remote servers securely",
                "scp transfers files between systems safely",
                "wget downloads files from web servers",
                "curl makes HTTP requests to APIs",
                "tar compresses multiple files together",
                "zip creates compressed archive files",
                "nginx serves web content efficiently",
                "apache handles HTTP requests properly",
                "mysql manages database operations",
                "git tracks source code changes",
                "docker runs containerized applications",
                "vim edits text files professionally",
                "nano provides simple text editing",
                "screen multiplexes terminal sessions",
                "tmux manages multiple shell sessions",
                "cron schedules automated tasks regularly",
                "systemctl controls system services",
                "mount attaches filesystem devices",
                "fdisk partitions storage devices",
                "lsblk lists block devices clearly",
                "df shows filesystem usage statistics",
                "du calculates directory sizes accurately",
                "ping tests network connectivity reliably",
                "netstat displays network connections",
                "iptables configures firewall rules",
                "rsync synchronizes files efficiently",
            ],
        ),
        # Conversational patterns - should all be False (35 examples)
        (
            "CONVERSATIONAL",
            False,
            [
                "Please help me configure the firewall",
                "Can you show me how to use Docker?",
                "Would you mind explaining Git workflow?",
                "Could you assist with database optimization?",
                "I'd like to learn about Kubernetes",
                "Would it be possible to automate deployments?",
                "Can we discuss security best practices?",
                "Please walk me through the setup process",
                "I'm having trouble with SSL configuration",
                "Could you recommend monitoring tools?",
                "Would you suggest backup strategies?",
                "Can you help troubleshoot network issues?",
                "Please explain load balancing concepts",
                "I need guidance on container orchestration",
                "Could we review the disaster recovery plan?",
                "Would you mind checking system logs?",
                "Can you verify the server configuration?",
                "Please confirm the backup completed successfully",
                "I'd appreciate help with performance tuning",
                "Could you investigate the connection timeout?",
                "Would you mind updating the documentation?",
                "Can we schedule a maintenance window?",
                "Please notify users about the downtime",
                "I think we should upgrade the hardware",
                "Could you consider implementing caching?",
                "Would it help to increase memory allocation?",
                "Can we try restarting the application server?",
                "Please make sure logging is enabled",
                "I wonder if we need more disk space",
                "Could you check if all services are running?",
                "Would you mind testing the backup restore?",
                "Can we validate the security patches?",
                "Please ensure compliance requirements are met",
                "I believe we should monitor CPU usage",
                "Could you double-check the network configuration?",
            ],
        ),
    ]

    print("=" * 80)
    print("COMPREHENSIVE SHELL COMMAND DETECTOR TEST (100+ CASES)")
    print("=" * 80)

    total_tests = 0
    total_errors = 0

    for category, expected, test_inputs in test_cases:
        print(f"\n📁 {category} (Expected: {expected})")
        print("-" * 60)

        category_errors = 0
        for test_input in test_inputs:
            result = detector.is_shell_command(test_input)
            total_tests += 1

            if result != expected:
                status = "❌ WRONG"
                category_errors += 1
                total_errors += 1
            else:
                status = "✅ OK"

            print(f"{status:8} | '{test_input}' -> {result}")

        # Category summary
        accuracy = ((len(test_inputs) - category_errors) / len(test_inputs)) * 100
        print(
            f"\n📊 Category Accuracy: {accuracy:.1f}% ({len(test_inputs) - category_errors}/{len(test_inputs)})"
        )

    # Overall summary
    print("\n" + "=" * 80)
    overall_accuracy = ((total_tests - total_errors) / total_tests) * 100
    print(
        f"🎯 OVERALL ACCURACY: {overall_accuracy:.1f}% ({total_tests - total_errors}/{total_tests})"
    )
    print(f"❌ Total Errors: {total_errors}")
    print(f"📊 Total Test Cases: {total_tests}")
    print("=" * 80)


if __name__ == "__main__":
    main()
