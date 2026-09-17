import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { login as loginRequest, register as registerRequest } from '../../api/auth'
import { applyApiErrors } from '../../utils/apiErrors'
import { setTokens } from '../../utils/authTokens'
import { Alert, Box, Button, FormField, Input } from '../common_ui'

const registerSchema = z
  .object({
    email: z.string().trim().email('Enter a valid email'),
    first_name: z.string().trim().min(1, 'First name is required'),
    last_name: z.string().trim().optional().or(z.literal('')),
    password: z.string().min(8, 'Password must be at least 8 characters'),
    password_confirm: z.string().min(1, 'Please confirm your password'),
  })
  .refine((data) => data.password === data.password_confirm, {
    message: 'Passwords do not match',
    path: ['password_confirm'],
  })

export default function RegisterForm() {
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: '',
      first_name: '',
      last_name: '',
      password: '',
      password_confirm: '',
    },
  })

  const onSubmit = async (values) => {
    try {
      await registerRequest({
        email: values.email,
        first_name: values.first_name,
        last_name: values.last_name || '',
        password: values.password,
        password_confirm: values.password_confirm,
      })

      // Register does not return JWTs — sign in immediately after.
      const { data } = await loginRequest({
        email: values.email,
        password: values.password,
      })
      setTokens(data)
      window.location.assign('/')
    } catch (error) {
      applyApiErrors(error, setError)
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate>
      {errors.root && (
        <Alert variant="danger" className="py-2">
          {errors.root.message}
        </Alert>
      )}

      <FormField id="register-email" label="Email" error={errors.email?.message}>
        <Input
          id="register-email"
          type="email"
          autoComplete="email"
          invalid={Boolean(errors.email)}
          {...register('email')}
        />
      </FormField>

      <Box className="row">
        <FormField
          id="register-first-name"
          label="First name"
          error={errors.first_name?.message}
          className="col-md-6"
        >
          <Input
            id="register-first-name"
            type="text"
            autoComplete="given-name"
            invalid={Boolean(errors.first_name)}
            {...register('first_name')}
          />
        </FormField>

        <FormField
          id="register-last-name"
          label={
            <>
              Last name <span className="text-muted">(optional)</span>
            </>
          }
          error={errors.last_name?.message}
          className="col-md-6"
        >
          <Input
            id="register-last-name"
            type="text"
            autoComplete="family-name"
            invalid={Boolean(errors.last_name)}
            {...register('last_name')}
          />
        </FormField>
      </Box>

      <FormField
        id="register-password"
        label="Password"
        error={errors.password?.message}
      >
        <Input
          id="register-password"
          type="password"
          autoComplete="new-password"
          invalid={Boolean(errors.password)}
          {...register('password')}
        />
      </FormField>

      <FormField
        id="register-password-confirm"
        label="Confirm password"
        error={errors.password_confirm?.message}
      >
        <Input
          id="register-password-confirm"
          type="password"
          autoComplete="new-password"
          invalid={Boolean(errors.password_confirm)}
          {...register('password_confirm')}
        />
      </FormField>

      <Button type="submit" block disabled={isSubmitting}>
        {isSubmitting ? 'Creating account…' : 'Create account'}
      </Button>
    </form>
  )
}
