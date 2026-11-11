import { Effect, Schema, Stream } from 'effect';
import { ChildProcess, CommandLine } from 'effect/process';

export class CommandError extends Schema.TaggedError<CommandError>()('CommandError', {
	message: Schema.String
}) {}

export const exec = Effect.fn('exec')(function* (command: ChildProcess.StandardCommand) {
	const handle = yield* command;

	const [stdout, stderr, exitCode] = yield* Effect.all(
		[
			Stream.mkString(Stream.decodeText(handle.stdout)),
			Stream.mkString(Stream.decodeText(handle.stderr)),
			handle.exitCode
		],
		{ concurrency: 'unbounded' }
	);

	return { stdout, stderr, exitCode };
}, Effect.scoped);

export const run = Effect.fn('run')(function* (command: ChildProcess.StandardCommand) {
	const { stdout, stderr, exitCode } = yield* exec(command);

	if (exitCode !== 0)
		return yield* new CommandError({
			message: `${CommandLine.display([command.command, ...command.args])} exited with ${exitCode}: ${stderr}`
		});

	return stdout;
});
