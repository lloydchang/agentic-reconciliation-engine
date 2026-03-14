fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: <skill> <input>");
        std::process::exit(1);
    }
    let input = &args[1];
    println!("network-diagnostics Rust Skill Output for input: {}", input);
}

